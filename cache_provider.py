class FSCacheProviderBase:
    """
    this is base class for cache provider. we can implement it for a verity of cache providers
    """

    def __init__(self, connection_info=None):
        self.connection_info = connection_info

    def connect_to_cache(self):
        pass

    def disconnect_from_cache(self):
        pass

    def create_feature_in_cache(self, feature_name):
        raise Exception("not implemented")

    def insert_data_to_feature(self, feature_name, key, value):
        raise Exception("not implemented")

    def get_feature_record(self, feature_name, key):
        raise Exception("not implemented")

    def get_all_feature_records(self, feature_name):
        raise Exception("not implemented")

    def delete_feature_record(self, feature_name):
        pass


class LocalFSCacheProvider(FSCacheProviderBase):

    def __init__(self, logger):
        super(LocalFSCacheProvider).__init__()
        self.supported_feature = []
        self.logger = logger
        self.abs_cache = {}

    def create_feature_in_cache(self, feature_name):
        if feature_name not in self.abs_cache:
            self.logger.info('Adding feature name %s to cache', feature_name)
            self.abs_cache[feature_name] = {}
            self.supported_feature.append(feature_name)
        else:
            self.logger.debug('feature name %s already in cache', feature_name)

    def insert_data_to_feature(self, feature_name, key, value):

        if feature_name in self.abs_cache:
            self.abs_cache[feature_name][key] = value
        else:
            self.logger.error('feature name %s not in cache!', feature_name)

    def get_feature_record(self, feature_name, key):

        if feature_name in self.abs_cache:
            if key in self.abs_cache[feature_name]:
                return self.abs_cache.get(feature_name)[key]
            else:
                self.logger.error('key %s not in cache feature name!', key, feature_name)
        else:
            self.logger.error('feature name %s not in cache!', feature_name)

        return None

    def get_all_feature_records(self, feature_name):
        return self.abs_cache.get(feature_name)
