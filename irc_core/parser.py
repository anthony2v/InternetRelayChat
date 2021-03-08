def serialize_message(msg, *params, prefix=None):
    """Serializes a message from higher-level python
    to a IRC message packet.
    
    NOTE: \\r\\n terminator is added by connection class
    """
    serialized = ''
    if prefix is not None:
        serialized += ':%s ' % prefix
    
    serialized += msg
    for i, param in enumerate(params):
        if '\r' in param or '\n' in param:
            raise ValueError('parameters may not contain \\r or \\n')
        if ' ' in param:
            if i != len(params) - 1:
                raise ValueError('only the final parameter may contain spaces')
            serialized += ' :%s' % param
        else:
            serialized += ' %s' % param
    
    serialized = serialized.encode('ascii')

    return serialized

def parse_message(message):
    """Parse a bytes message to its string parts.

    Returns:
        command_code, parameter_list, prefix
    """
    message = message.decode()

    message = message.replace("\r\n", "")

    prefix = None
    if message.startswith(':'):
        first_space = message.index(' ')
        prefix = message[1:first_space]
        message = message[first_space+1:].lstrip(' ')

    trailing_start = message.find(':')
    trailing = []
    if trailing_start != -1:   
        trailing.append(message[trailing_start+1:])
        message = message[:trailing_start]

    cmd, *params = message.split(' ')
    params = list(p for p in params if p)

    params += trailing

    return cmd, prefix, params