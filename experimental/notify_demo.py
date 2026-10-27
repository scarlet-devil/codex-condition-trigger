"""Reproducible G1 two-batch demo. Uses only temporary files and the fake adapter."""
import contextlib
import argparse
import io
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from test_notify import NotifyFixture  # noqa: E402
import notify_state as ns  # noqa: E402


def scenario(mode):
    fixture=NotifyFixture()
    fixture.setUp()
    try:
        fixture.open(mode)
        a=fixture.batch('synthetic A');fixture.tick()
        b=fixture.batch('synthetic B');fixture.tick()
        while_running=len(fixture.fake.sent)
        fixture.finish()
        for _ in range(4):fixture.tick()
        rows=fixture.store.rows()
        return dict(mode=mode,files_are_synthetic=True,ipc_calls=0,model_calls=0,
            sends_while_a_running=while_running,adapter_sends=len(fixture.fake.sent),
            sent_b_once=fixture.fake.sent.count(b)==1,first_batch_retained=rows[0]['id']==a,
            first_state=rows[0]['state'],business_ack=False,
            delivered=sum(r['state']=='delivered' for r in rows),
            backlog=len(ns.pending(fixture.store)) if mode=='notify' else len(rows))
    finally:
        fixture.doCleanups()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--temp-parent',type=Path)
    args=parser.parse_args()
    if args.temp_parent:
        args.temp_parent.mkdir(parents=True,exist_ok=True)
        tempfile.tempdir=str(args.temp_parent.resolve())
    with contextlib.redirect_stdout(io.StringIO()):
        result=[scenario('notify'),scenario('verified_delivery')]
    assert result[0]['adapter_sends']==2 and result[1]['adapter_sends']==1
    assert all(r['delivered']==0 and r['sends_while_a_running']==1 for r in result)
    print(json.dumps(result,indent=2))
