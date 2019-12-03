def str_to_dict(str1, sep=':'):
    dict1 = {}
    for line in str1.splitlines(True):
        if line.strip():
            p = line.find(sep)
            # print '"'+line[:p]+'":"'+line[p+1:]+'",'
            # print '"'+line[:p]+'":"'+line[p+1:-1]+'",\n',
            dict1[line[:p].strip()] = line[p + 1:-1].strip()
    # print_json(dict1)
    return dict1

def typed_property(name, expected_type, default_value=None):
    storage_name = '_' + name

    @property
    def prop(self):
        return getattr(self, storage_name, default_value)

    @prop.setter
    def prop(self, value):
        if isinstance(expected_type, list):
            if name not in expected_type:
                raise TypeError('{} must be in {}'.format(name, ','.join(expected_type)))
        if not isinstance(value, expected_type):
            raise TypeError('{} must be a {}'.format(name, expected_type))
        setattr(self, storage_name, value)

    @prop.deleter
    def first_name(self):
        raise AttributeError("Can't delete attribute")

    return prop