import markdown


class Bastard(dict):

    """ Magical dict to (try to) generate links on demand """

    loader = None

    def __contains__(self, key):
        import pudb; pudb.set_trace()
        if not super(Bastard, self).__contains__(key):

            if self._valid_magickey(key):
                
                storable, handle = key.split('/')
                try:
                    return bool(self.loader(storable, handle))
                except:
                    return False

            return False

        return True
    
    
    def __getitem__(self, key):

        if not super(Bastard, self).__contains__(key):

            if self._valid_magickey(key):

                storable, handle = key.split('/')
                try:
                    instance = self.loader(storable, handle)

                    try:
                        url = instance.url('full')
                    except:

                        try:
                            url = instance.url('teaser')
                        except:
                            url = "NOLINK" # FIXME: What's the more elegant version of this, again?

                    return (url, instance.title if hasattr(instance, 'title') else None)

                except:
                    raise KeyError("Couldn't load '%s.%s'." % storable, handle)


        return super(Bastard, self).__getitem__(key)


    def _valid_magickey(self, key):

        return '/' in key and len(key.split('/')) == 2


    def set_loader(self, loader):
        self.loader = loader



class pdnMarkdown(markdown.Markdown):

    def __init__(self, *args, **kwargs):
        
        super(pdnMarkdown, self).__init__(*args, **kwargs)
        self.references = Bastard()
