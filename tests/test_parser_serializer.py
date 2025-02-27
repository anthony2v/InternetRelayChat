import pytest

from irc_core.parser import serialize_message

def test_no_params_no_prefix():
    assert serialize_message('NICK') == b'NICK'

def test_no_params_with_prefix():
    assert serialize_message('NICK', prefix='WiZ') == b':WiZ NICK'

def test_all_params_no_spaces_no_prefix():
    assert serialize_message(
        'NICK', 'one', 'two', 'three') == b'NICK one two three'

def test_all_params_no_spaces_except_last_no_prefix():
    assert serialize_message(
        'NICK', 'one', 'two', 'three four five') == b'NICK one two :three four five'

def test_some_params_contain_cr_or_lf():
    with pytest.raises(ValueError):
        serialize_message(
            'NICK', 'one two \n three')

    with pytest.raises(ValueError):
        serialize_message(
            'NICK', 'one two \r three')

def test_spaces_in_param_that_is_not_the_last_one():
    with pytest.raises(ValueError):
        serialize_message(
            'NICK', 'one two', 'three')
