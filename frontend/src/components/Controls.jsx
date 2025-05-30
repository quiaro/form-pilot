import React, { useState } from 'react';

function Controls({ categories, onSubmit, loading }) {
  const [selectedCategory, setSelectedCategory] = useState('');

  const handleCategoryChange = (e) => {
    setSelectedCategory(e.target.value);
  };

  const handleSubmit = () => {
    if (selectedCategory) {
      onSubmit(selectedCategory);
    }
  };

  return (
    <div className="controls">
      <div className="control-row">
        <select
          value={selectedCategory}
          onChange={handleCategoryChange}
          disabled={loading}
          className="category-select"
        >
          <option value="" disabled>
            Select category
          </option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
        <button
          onClick={handleSubmit}
          disabled={!selectedCategory || loading}
          className="submit-button"
        >
          {loading ? (
            <>
              <span className="loading"></span>
              Processing...
            </>
          ) : (
            'Show me trending information'
          )}
        </button>
      </div>
    </div>
  );
}

export default Controls;
