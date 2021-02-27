def serialize_message(msg, *params, prefix=None):
    serialized = b''
    if prefix is not None:
        serialized += b':%b ' % prefix
    
    serialized += msg
    for i, param in enumerate(params):
        if b'\r' in param or b'\n' in param:
            raise ValueError('parameters may not contain \\r or \\n')
        if b' ' in param:
            if i != len(params) - 1:
                raise ValueError('only the final parameter may contain spaces')
            serialized += b' :%b' % param
        else:
            serialized += b' %b' % param
    
    return serialized