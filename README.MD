
get- /users/create
get- /users/{user_id}
put - /users/{user_id}

get - /wallet/{user_id}/balance 
post - /wallet/{user_id}/add-money
post - /wallet/{user_id}/withdraw-money

get - /wallet/{user_id}/transactions
get - /transactions/detail/{transaction_id}


post - /transfer


Run application : uvicorn app:app --reload  