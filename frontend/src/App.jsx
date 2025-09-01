import { useState,useEffect, use } from 'react'
import axios from 'axios'


function App() {
  const [user, setUser] = useState({
    username: "",
    email: "",
    balance: 0.0,
    password: "",
    phone_number: "",
    created_at: new Date(),
    updated_at: new Date()
  });
  const [checkBalance, setCheckBalance] = useState(false);

  useEffect(() => {
      checkBalancefun();
  }, [user._id]);

  function createUser() {
  
    axios.post("http://localhost:8000/users/create", user)
      .then(response => {
        console.log("User created:", response.data);
      })
      .catch(error => {
        console.error("Error creating user:", error);
      });
  }

const checkBalancefun = () => {
  let userId;
  if (!user._id) {
   userId = '68b594652ff10f045ecdf5b6';
  }else{
    userId = user._id
  }
  axios.get(`http://localhost:8000/wallet/${userId}/balance`)
    .then(response => {
      setCheckBalance(response.data);
    })
    .catch(error => {
      console.error("Error checking balance:", error);
    });
}

  return (
    <>
    <div>
      <h1>Create User</h1>
      <input label='username'></input>
      <input label='email'></input>
      <input label='password'></input>
      <input label='phone number'></input>
     <button onClick={createUser}>Create User</button>
     </div>
      <div>
        <h1>Check Balance</h1>
        <button onClick={checkBalancefun}>Check Balance</button>
        {checkBalance && (
          <div>
            <p>Balance: {checkBalance?.balance}</p>
            <p>Last Updated: {checkBalance?.last_updated}</p>
          </div>
        )}
      </div>

    </>
  )
}

export default App
