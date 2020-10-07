# lemonade_feature_store
Implementation of minimal working feature store base on Lemonade home assignment

# How in run the program?

First, kill all processes running on port 5000 and 4000
find those processes with: sudo lsof -i:<port>
Then kill them with: kill -9 <pid>
	
1. clone the project to a local dir
2. run in terminal (from rep dir) > python3 app.py (listening to port 5000)
3. run in terminal (from rep dir) > python3 feature_store_app.py (listening to port 4000)

Feature Store is ready to go.

# API

Now, you can use the following API to get data from feature store:

POST 127.0.0.1:4000/featureInference

valid request example:
{
	"featureName" : "payment_transaction_type",
	"baseFeature": 10
}

example response:
{
    "featureInference": "PREPAID"
}

POST 127.0.0.1:4000/featureTraining

valid request example:
{
	"featureName" : "payment_transaction_type"
}

GET 127.0.0.1:4000/featureDiscovery

example response:
{
    
    "feature_discovery": [
        "user_payment_transaction_time",
        "user_failed_transactions_count",
        "quote_creation_binding_time",
        "payment_transaction_type"
    ]
}


