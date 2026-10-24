"""Local-only traceback projection for an already rejected cwd check."""
import desktop_ipc as ipc


def cwd_values(error, validator_code):
    if type(error) is not ipc.ProtocolCheckError or error.reason != 'snapshot_cwd_mismatch':
        return None
    trace = error.__traceback__
    while trace is not None:
        if trace.tb_frame.f_code is validator_code:
            fields = trace.tb_frame.f_locals
            state, expected = fields.get('state'), fields.get('expected_cwd')
            if isinstance(state, dict) and isinstance(expected, str) and isinstance(state.get('cwd'), str):
                return {'expected_cwd': expected, 'native_cwd': state['cwd']}
            return None
        trace = trace.tb_next
    return None
