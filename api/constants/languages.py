language_timezone_mapping = {
    "en-US": "America/New_York",
    "zh-Hans": "Asia/Shanghai"
}

languages = list(language_timezone_mapping.keys())


def supported_language(lang):
    if lang in languages:
        return lang

    error = "{lang} is not a valid language.".format(lang=lang)
    raise ValueError(error)
