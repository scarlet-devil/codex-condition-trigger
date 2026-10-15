"""Thin stdio client for Hub material-recovery-v1. No credentials or HTTP."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

MAX_FILE=8*1024*1024


def exchange(request, config, client):
    from drive_exchange_local_hub import canonical_json_bytes as encode, project_identity_for_root
    if request.get('schema')!=1 or request.get('action') not in ('lookup','upload','readback'):
        raise ValueError('invalid action')
    root=Path(config['project_root']).resolve(strict=True)
    marker=json.loads((root/'.drive-exchange/project.json').read_bytes())
    project=marker['project_id'];route=marker['route']
    if project!=config['project_id'] or route!=config['route_name']:
        raise ValueError('registered project or route changed')
    name=request['name']
    if not isinstance(name,str) or not name or Path(name).name!=name or '/' in name or '\\' in name:
        raise ValueError('invalid logical name')
    source=Path(request['path']).resolve(strict=True)
    # The candidate activation fixes exactly one approved frozen outbox root.
    frozen=Path(config['frozen_root']).resolve(strict=True)
    if frozen not in source.parents or source.stat().st_size>MAX_FILE:
        raise ValueError('source is outside the registered outbox or exceeds 8 MiB')
    raw=source.read_bytes()
    if len(raw)!=request['size'] or hashlib.sha256(raw).hexdigest()!=request['sha256']:
        raise ValueError('frozen source changed')
    descriptor={k:request[k] for k in ('key','batch_id','manifest_sha256','parent_id','name','sha256','size')}
    path=('work-materials/'+name).encode('utf-8')
    manifest=encode(dict(schema_version='drive-exchange-manifest-v1',project_id=project,route=route,
        files=[dict(path=path.decode(),byte_size=len(raw),sha256=request['sha256'])]))
    frame=b'DXSTAGE\x00\x01'+struct.pack('>Q',len(manifest))+manifest+struct.pack('>I',len(path))+path+struct.pack('>Q',len(raw))+raw
    identity=project_identity_for_root(root)
    operation='op_'+hashlib.sha256(encode([project,identity,route,request['key']])).hexdigest()[:32]
    inner=dict(schema_version='drive-exchange-local-request-v1',operation_id=operation,project_id=project,
        project_identity=identity,route_name=route,mode='submit',manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        frame_sha256=hashlib.sha256(frame).hexdigest())
    response=client.exchange(encode(dict(schema_version='drive-exchange-material-recovery-v1',action=request['action'],
                                       request=inner,descriptor=descriptor)),frame)
    if request['action']=='readback' and response.get('file_id')!=request.get('file_id'):
        raise ValueError('unexpected remote ID')
    return response


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    config=json.loads(Path(args.config).read_bytes())
    # The operator supplies the installed Hub library on PYTHONPATH. This client
    # cannot construct a provider or a new Hub, start one, or handle OAuth.
    from drive_exchange_local_hub.ipc import NamedPipeHubClient, default_pipe_name
    request=json.loads(sys.stdin.buffer.read(65537))
    result=exchange(request,config,NamedPipeHubClient(pipe_name=default_pipe_name()))
    print(json.dumps(result,ensure_ascii=False,separators=(',',':')))


if __name__=='__main__':
    try: main()
    except Exception as error:
        print(json.dumps({'status':'unknown','error_type':type(error).__name__}))
        raise SystemExit(1)
