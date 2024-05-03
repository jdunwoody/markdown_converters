import re


def should_skip(text: str) -> bool:
    if len(text) == 0:
        return True

    re_num_currency_percent = r"^[-$]?['`,.\d ]*[?%]?$"
    if re.findall(re_num_currency_percent, text):
        return True

    re_one_or_two_short_words = r"^\w{,3}( \w{,3})?$"
    if re.findall(re_one_or_two_short_words, text):
        return True

    re_date = r"^[(]?[12]\d{,3}[)]?$"
    if re.findall(re_date, text):
        return True

    return False
