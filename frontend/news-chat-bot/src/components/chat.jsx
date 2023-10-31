import React, { useState } from 'react';
import axios from 'axios';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');

  const sendMessage = async () => {
    const newMessage = { role: 'user', content: userInput };
    setMessages([...messages, newMessage]);
    setUserInput('');
  
    try {
      // Your axios request here
      const response = await axios.post('http://localhost:5000/query', { messages: [...messages, newMessage] });
  
      let responseData;
  
      try {
        responseData = JSON.parse(response.data.response);
        console.log(responseData.data)
      } catch (error) {
        responseData = response.data.response; // Treat it as plain text
      }
  
      if (Array.isArray(responseData)) {
        responseData.forEach((article, index) => {
          const sentence = `Title: ${article.title}, Author: ${article.author}`;
          const botResponse = { role: 'system', content: sentence };
          setTimeout(() => {
            setMessages(prevMessages => [...prevMessages, botResponse]);
          }, index * 1000); // Delay each sentence by 1 second
        });
      } else {
        const botResponse = { role: 'system', content: responseData };
        setMessages(prevMessages => [...prevMessages, botResponse]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };
  
  
  
  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={message.role}>
            {message.content}
          </div>
        ))}
      </div>
      <div className="input-container">
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="Type a message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default Chat;
