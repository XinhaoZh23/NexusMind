import Layout from './components/Layout';
import ChatHistory from './components/ChatHistory';
import MessageInput from './components/MessageInput';

function App() {
  return (
    <Layout>
      <ChatHistory />
      <MessageInput />
    </Layout>
  );
}

export default App;
