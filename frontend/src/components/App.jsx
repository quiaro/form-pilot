import React, { useState, useRef, useEffect } from 'react';
import Controls from './Controls';
import Content from './Content';
import Header from './Header';

function App() {
  const [trendingData, setTrendingData] = useState('');
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef(null);

  const [categories, setCategories] = useState([]);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('/api/categories');
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        const data = await response.json();
        setCategories(data.categories);
      } catch (error) {
        console.error('Failed to fetch categories:', error);
      }
    };

    fetchCategories();
  }, []);

  // Cleanup function for in-progress requests
  useEffect(() => {
    return () => {
      // Abort any in-progress fetch when component unmounts
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const fetchTrendingData = async (category) => {
    setLoading(true);
    setTrendingData('');

    // Abort any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create an AbortController to handle cleanup
    const controller = new AbortController();
    const signal = controller.signal;
    abortControllerRef.current = controller;

    try {
      const response = await fetch(
        `/api/trending/${encodeURIComponent(category)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
          },
          signal, // Add the abort signal
        }
      );

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done, value;

      while (!done) {
        ({ value, done } = await reader.read());
        if (signal.aborted || done) break;

        const text = decoder.decode(value, { stream: true });
        setTrendingData((prev) => prev + text);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setTrendingData('Error fetching trending data. Please try again.');
    } finally {
      if (!signal.aborted) {
        setLoading(false);
        // Clear the abortControllerRef if this request is complete and not aborted
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    }
  };

  return (
    <div className="container">
      <Header />
      {categories.length > 0 && (
        <>
          <Controls
            categories={categories}
            onSubmit={fetchTrendingData}
            loading={loading}
          />
          <Content data={trendingData} loading={loading} />
        </>
      )}
    </div>
  );
}

export default App;
