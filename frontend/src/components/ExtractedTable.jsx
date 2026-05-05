import React, { useState } from 'react';

const ExtractedTable = ({ data, loading }) => {
  const [showNotification, setShowNotification] = useState(null);

  if (loading) {
    return <div className="loading">Loading data...</div>;
  }

  if (!data || !data.items || data.items.length === 0) {
    return null;
  }

  const items = data.items;
  const totalAmount = data.total_amount || 0;
  const itemCount = data.item_count || items.length;

  // Calculate total GST
  const totalGST = items.reduce((sum, item) => {
    const itemGST = (item.total_amount || 0) * ((item.gst_percent || 0) / 100);
    return sum + itemGST;
  }, 0);

  /**
   * Get category badge color
   */
  const getCategoryBadgeStyle = (category) => {
    const styles = {
      'Stationery': '#8b5cf6', // Purple
      'IT Supply': '#14b8a6', // Teal
      'Furniture': '#f59e0b', // Amber
      'Hygiene': '#3b82f6', // Blue
      'General': '#6b7280', // Gray
    };
    return styles[category] || '#6b7280';
  };

  /**
   * Get confidence color
   */
  const getConfidenceColor = (score) => {
    if (score >= 0.9) return '#10b981'; // Green
    if (score >= 0.7) return '#f59e0b'; // Amber
    return '#ef4444'; // Red
  };

  /**
   * Get confidence percentage
   */
  const getConfidencePercent = (score) => {
    return Math.round(score * 100);
  };

  /**
   * Export to CSV
   */
  const handleExportCSV = () => {
    try {
      // Create CSV headers
      const headers = [
        '#',
        'Item Name',
        'Category',
        'HSN Code',
        'Quantity',
        'Unit',
        'Unit Rate',
        'GST %',
        'Total Amount',
        'Confidence',
      ];

      // Create CSV rows
      const rows = items.map((item, idx) => [
        idx + 1,
        item.item_name || '',
        item.category || '',
        item.hsn_code || '',
        item.quantity || '',
        item.unit || '',
        item.unit_rate?.toFixed(2) || '',
        item.gst_percent || '',
        item.total_amount?.toFixed(2) || '',
        getConfidencePercent(item.confidence_score) + '%',
      ]);

      // Add summary rows
      rows.push([]);
      rows.push(['Total', '', '', '', '', '', '', '', totalAmount.toFixed(2), '']);
      rows.push(['Total GST', '', '', '', '', '', '', '', totalGST.toFixed(2), '']);

      // Convert to CSV string
      const csvContent = [
        headers.join(','),
        ...rows.map((row) =>
          row
            .map((cell) => {
              // Escape commas and quotes in cells
              if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"'))) {
                return `"${cell.replace(/"/g, '""')}"`;
              }
              return cell;
            })
            .join(',')
        ),
      ].join('\n');

      // Create blob and download
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice-items-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setShowNotification('CSV exported successfully!');
      setTimeout(() => setShowNotification(null), 3000);
    } catch (error) {
      console.error('Export failed:', error);
      setShowNotification('Export failed!');
      setTimeout(() => setShowNotification(null), 3000);
    }
  };

  /**
   * Handle approve and save
   */
  const handleApproveAndSave = () => {
    setShowNotification('Data saved and approved!');
    setTimeout(() => setShowNotification(null), 3000);
  };

  return (
    <div className="extracted-table-container">
      {/* Notification */}
      {showNotification && (
        <div className="notification-banner">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
          </svg>
          <span>{showNotification}</span>
        </div>
      )}

      {/* Header */}
      <div className="table-header">
        <h2>Extracted Line Items</h2>
        <div className="header-actions">
          <button onClick={handleExportCSV} className="btn-export" title="Export to CSV">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
              <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            Export CSV
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon invoice"></div>
          <div className="card-content">
            <p className="card-label">Total Items</p>
            <p className="card-value">{itemCount}</p>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon amount"></div>
          <div className="card-content">
            <p className="card-label">Total Amount</p>
            <p className="card-value">₹{totalAmount.toFixed(2)}</p>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon gst"></div>
          <div className="card-content">
            <p className="card-label">Total GST</p>
            <p className="card-value">₹{totalGST.toFixed(2)}</p>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon confidence"></div>
          <div className="card-content">
            <p className="card-label">Avg Confidence</p>
            <p className="card-value">
              {(
                (items.reduce((sum, item) => sum + (item.confidence_score || 0), 0) / items.length) *
                100
              ).toFixed(0)}
              %
            </p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table className="extracted-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Item Name</th>
              <th>Category</th>
              <th>HSN Code</th>
              <th>Qty</th>
              <th>Unit</th>
              <th>Unit Rate</th>
              <th>GST%</th>
              <th>Total Amount</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={index} className="table-row">
                <td className="row-number">{index + 1}</td>
                <td className="item-name">{item.item_name || '-'}</td>
                <td className="category-cell">
                  <span
                    className="category-badge"
                    style={{ backgroundColor: getCategoryBadgeStyle(item.category) }}
                  >
                    {item.category || 'General'}
                  </span>
                </td>
                <td className="hsn-code">{item.hsn_code || '-'}</td>
                <td className="quantity">{item.quantity || '-'}</td>
                <td className="unit">{item.unit || '-'}</td>
                <td className="unit-rate">₹{item.unit_rate ? item.unit_rate.toFixed(2) : '0.00'}</td>
                <td className="gst-percent">{item.gst_percent || '-'}%</td>
                <td className="total-amount">₹{item.total_amount ? item.total_amount.toFixed(2) : '0.00'}</td>
                <td className="confidence-cell">
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{
                        width: `${getConfidencePercent(item.confidence_score)}%`,
                        backgroundColor: getConfidenceColor(item.confidence_score),
                      }}
                    ></div>
                  </div>
                  <span className="confidence-text">
                    {getConfidencePercent(item.confidence_score)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="table-footer">
        <div className="footer-summary">
          <div className="summary-item">
            <span>Subtotal:</span>
            <strong>₹{totalAmount.toFixed(2)}</strong>
          </div>
          <div className="summary-item">
            <span>Total GST:</span>
            <strong>₹{totalGST.toFixed(2)}</strong>
          </div>
          <div className="summary-item total">
            <span>Grand Total:</span>
            <strong>₹{(totalAmount + totalGST).toFixed(2)}</strong>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="table-actions">
        <button onClick={handleApproveAndSave} className="btn-approve">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
            <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          Approve & Save
        </button>
      </div>
    </div>
  );
};

export default ExtractedTable;
