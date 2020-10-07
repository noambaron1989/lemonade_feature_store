import datetime
import logging
import os
import sqlite3

from flask import Flask, request, abort

from cache_provider import LocalFSCacheProvider

app = Flask(__name__)

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FeatureStore:
    user_payment_transaction_time = 'user_payment_transaction_time'
    user_failed_transactions_count = 'user_failed_transactions_count'
    quote_creation_binding_time = 'quote_creation_binding_time'
    payment_transaction_type = 'payment_transaction_type'

    def __init__(self, dw_conn, cache_prov):
        self.dw_conn = dw_conn
        self.cache_provider: LocalFSCacheProvider = cache_prov

    def insert_feature_batch_to_cache(self):
        """
        This method should be called once every chron time. In this example, only once
        """
        logger.info('inserting feature batch to cache')

        for curr_feature_name in [self.user_payment_transaction_time,
                                  self.user_failed_transactions_count,
                                  self.quote_creation_binding_time,
                                  self.payment_transaction_type]:
            self.cache_provider.create_feature_in_cache(curr_feature_name)

        self.insert_user_id_based_features()

        self.insert_quote_id_based_features()

        self.insert_payment_trans_based_features()

    def insert_payment_trans_based_features(self):
        logger.debug('inserting payment_trans id based features...')

        payment_trans_ids_res = get_records(self.dw_conn, 'SELECT id FROM payment_transaction')
        logger.debug('found %s payment_trans id records ' % len(payment_trans_ids_res))
        if payment_trans_ids_res:
            payment_trans_ids_list = list(map(lambda x: x[0], payment_trans_ids_res))
            for curr_payment_trans_id in payment_trans_ids_list:
                payment_trans_type = self.get_type_of_payment(curr_payment_trans_id)
                self.cache_provider.insert_data_to_feature(feature_name=self.payment_transaction_type,
                                                           key=curr_payment_trans_id,
                                                           value=payment_trans_type)

    def insert_quote_id_based_features(self):
        logger.debug('inserting quote id based features...')

        quote_ids_res = get_records(self.dw_conn, 'SELECT id FROM quote')
        logger.debug('found %s quote id records ' % len(quote_ids_res))
        if quote_ids_res:
            quote_ids_list = list(map(lambda x: x[0], quote_ids_res))
            for curr_quote_id in quote_ids_list:
                time_from_quote_creation_to_binding = self.get_time_from_quote_creation_to_binding(curr_quote_id)
                self.cache_provider.insert_data_to_feature(feature_name=self.quote_creation_binding_time,
                                                           key=curr_quote_id,
                                                           value=time_from_quote_creation_to_binding)

    def insert_user_id_based_features(self):
        logger.debug('inserting user id based features...')

        user_id_res = get_records(self.dw_conn, 'select id from user')
        logger.debug('found %s user id records ' % len(user_id_res))
        if user_id_res:
            user_id_list = list(map(lambda x: x[0], user_id_res))
            for curr_user_id in user_id_list:
                user_payment_transaction_time = self.get_user_payment_transaction_time(curr_user_id)
                user_failed_transactions = self.get_user_failed_transactions(curr_user_id)
                self.cache_provider.insert_data_to_feature(feature_name=self.user_payment_transaction_time,
                                                           key=curr_user_id,
                                                           value=user_payment_transaction_time)
                self.cache_provider.insert_data_to_feature(feature_name=self.user_failed_transactions_count,
                                                           key=curr_user_id,
                                                           value=user_failed_transactions)

    def get_user_payment_transaction_time(self, user_id):
        """
        Calculate user payment transaction time. payment transaction connected to user via policy id.
        Each user can have more then 1 policy id. in this implementation I assumed we want to get payment_transaction
        for the policy id with maximum id number (assuming the most updated id is the relevant one)
        Of course we can implement it differently
        """
        policy_record = get_records(self.dw_conn, 'select id from policy where user_id=%s' % user_id)
        if policy_record:
            max_policy_id = max(policy_record)
            payment_record = get_records(self.dw_conn, 'select time from payment_transaction '
                                                       'where policy_id=%s' % max_policy_id)
            if payment_record:
                return payment_record[0][0]

        return None

    def get_time_from_quote_creation_to_binding(self, quote_id):
        """
        Get time from quote create to binding in seconds
        """
        record = get_records(self.dw_conn, 'select create_time, bind_time from quote where id=%s' % quote_id)
        if record:
            try:
                create_time_str = record[0][0]
                bind_time_str = record[0][1]
                if create_time_str and bind_time_str:
                    create_time = datetime.datetime.strptime(record[0][0], '%Y-%m-%d %H:%M:%S.%f')
                    bind_time = datetime.datetime.strptime(record[0][1], '%Y-%m-%d %H:%M:%S.%f')
                    delta = bind_time - create_time
                    return delta.seconds
            except Exception as error:
                logger.error('failed to calculate time_from_quote_creation_to_binding for quote id %s due to %s',
                             quote_id, error)
        return None

    def get_user_failed_transactions(self, user_id):
        """
        get amount of failed transactions per user, connecting user to transactions via policy ids
        """
        policy_record = get_records(self.dw_conn, 'select id from policy where user_id=%s' % user_id)
        if policy_record:
            policies = ','.join([str(curr_pol) for curr_pol in policy_record[0]])
            transactions_record = get_records(self.dw_conn, 'select count(*) as count from payment_transaction '
                                                            'where policy_id in (%s) and success=0' % policies)
            if transactions_record:
                failed_transactions_count = transactions_record[0][0]
                return failed_transactions_count
        return None

    def get_type_of_payment(self, payment_trans_id):
        payment_record = get_records(self.dw_conn, 'select payment_type from payment_transaction '
                                                   'where id=%s' % payment_trans_id)
        if payment_record:
            payment_type = payment_record[0][0]
            return payment_type
        return None


def create_connection_to_warehouse():
    conn = None
    try:
        basedir = os.path.abspath(os.path.dirname(__file__))
        conn = sqlite3.connect(os.path.join(basedir,
                                            "data_warehouse.db"))
    except Exception as error:
        logger.error('Failed connecting to data warehouse sqlite due to %s', error)

    return conn


def get_records(conn, sqlite_select_query):
    try:
        cursor = conn.cursor()
        cursor.execute(sqlite_select_query)
        records = cursor.fetchall()
        cursor.close()
        return records
    except sqlite3.Error as error:
        logger.error("Failed to read data from sqlite table due to ", error)
    return None


cache_provider = LocalFSCacheProvider(logger)

data_warehouse_conn = create_connection_to_warehouse()
feature_store = FeatureStore(data_warehouse_conn, cache_provider)
feature_store.insert_feature_batch_to_cache()
data_warehouse_conn.close()


@app.route('/featureInference', methods=['POST'])
def feature_inference():
    message = request.get_json()
    feature_name = message.get('featureName')
    base_feature = message.get('baseFeature')
    supported = feature_store.cache_provider.supported_feature

    if feature_name is None or base_feature is None or feature_name not in supported:
        abort(400, description="Bad request! one of the following fields are missing: featureName, baseFeature "
                               "or featureName is not supported!\nSupported featureNames are:%s" % supported)
    feature_inf = feature_store.cache_provider.get_feature_record(feature_name, base_feature)
    return {'featureInference': feature_inf}


@app.route('/featureTraining', methods=['POST'])
def feature_training():
    message = request.get_json()
    feature_name = message.get('featureName')

    supported = feature_store.cache_provider.supported_feature
    if feature_name is None or feature_name not in supported:
        abort(400, description="Bad request! fields featureName is missing or not supported!"
                               "\nSupported featureNames are:%s" % supported)

    all_feature_records = feature_store.cache_provider.get_all_feature_records(feature_name)
    return {'featureTraining': all_feature_records}


@app.route('/featureDiscovery')
def feature_discovery():
    return {'feature_discovery': feature_store.cache_provider.supported_feature}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
