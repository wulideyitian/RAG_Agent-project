import { useState, useRef, useEffect } from 'react';
import { healthCheck } from './services/api';
import type { Message } from './types';
import './App.css';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 检查 API 连接状态
  useEffect(() => {
    const checkApiHealth = async () => {
      try {
        await healthCheck();
        setApiStatus('connected');
      } catch (error) {
        setApiStatus('disconnected');
      }
    };

    checkApiHealth();
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 组件卸载时取消请求
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const generateId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // 创建助手消息占位
    const assistantMessageId = generateId();
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      },
    ]);
// 发送非流式请求
    try {
      const { sendChatRequest } = await import('./services/api');
      const response = await sendChatRequest({
        query: userMessage.content,
        stream: false,
      });
      
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? { ...msg, content: response.response }
            : msg
        )
      );
    } catch (error) {
      console.error('请求失败:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `❌ 请求失败：${error instanceof Error ? error.message : '未知错误'}`,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="app">
      {/* 头部 */}
      <header className="app-header">
        <h1>💻 笔记本电脑智能问答助手</h1>
        <div className={`status-indicator ${apiStatus}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {apiStatus === 'connected' && '服务正常'}
            {apiStatus === 'disconnected' && '服务断开'}
            {apiStatus === 'checking' && '检查中...'}
          </span>
        </div>
      </header>

      {/* 消息列表 */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>欢迎使用笔记本智能问答助手！👋</h2>
            <p>我可以帮您：</p>
            <ul>
              <li>解答笔记本电脑的技术问题</li>
              <li>提供故障诊断建议</li>
              <li>推荐适合的笔记本型号</li>
              <li>解答配置和性能相关问题</li>
            </ul>
            <p className="hint">在下方输入您的问题，开始对话吧～</p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.role}`}
              >
                <div className="message-avatar">
                  {message.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-text">{message.content}</div>
                  <div className="message-time">
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* 输入区域 */}
      <div className="input-container">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="请输入您的问题..."
          disabled={isLoading || apiStatus === 'disconnected'}
          className="chat-input"
        />
        <button
          onClick={handleSendMessage}
          disabled={isLoading || !inputValue.trim() || apiStatus === 'disconnected'}
          className="send-button"
        >
          {isLoading ? (
            <span className="loading-spinner">思考中...</span>
          ) : (
            '发送'
          )}
        </button>
      </div>

      {/* 页脚 */}
      <footer className="app-footer">
        <p>基于 RAG 和 Agent 技术的智能客服系统</p>
      </footer>
    </div>
  );
}

export default App;
