import { useState } from 'react';
import './InputForm.css';

function InputForm({ onSubmit }) {
  const [topic, setTopic] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim()) {
      onSubmit(topic.trim());
    }
  };

  const exampleTopics = [
    'Propagation of disinformation by LLMs',
    'Quantum computing applications in cryptography',
    'Ethical implications of AI in healthcare',
    'Climate change mitigation strategies'
  ];

  return (
    <div className="input-form">
      <h2>Start Your Research</h2>
      <p className="subtitle">Enter a topic for comprehensive lecture research</p>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="topic">Research Topic</label>
          <input
            type="text"
            id="topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Propagation of disinformation by LLMs"
            required
          />
        </div>

        <button type="submit" className="btn-primary">
          Start Research
        </button>
      </form>

      <div className="examples">
        <h4>Example Topics:</h4>
        <ul>
          {exampleTopics.map((example, idx) => (
            <li key={idx} onClick={() => setTopic(example)}>
              {example}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default InputForm;
