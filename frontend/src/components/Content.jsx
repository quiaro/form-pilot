import React from 'react';

function Content({ data, loading }) {
  return (
    <div className="content">
      {loading && !data ? (
        <div className="content-message">
          <div className="content-loading">
            <div className="content-loading-spinner"></div>
            <p>Fetching trending information...</p>
          </div>
        </div>
      ) : data ? (
        <div>
          <div
            className="content-data"
            dangerouslySetInnerHTML={{ __html: data }}
          />
        </div>
      ) : (
        <div className="content-message">
          <p>Select a category and search.</p>
          <p className="content-hint">See the trending information here.</p>
        </div>
      )}
    </div>
  );
}

export default Content;
