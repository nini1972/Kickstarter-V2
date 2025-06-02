import React, { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useAppContext } from '../../context/AppContext';

const AddInvestmentModal = ({ isOpen, onClose }) => {
  const { addInvestment, projects, loading } = useAppContext();

  const [formData, setFormData] = useState({
    project_id: '',
    amount: '',
    investment_date: new Date().toISOString().split('T')[0],
    expected_return: '',
    notes: '',
    reward_tier: ''
  });

  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.project_id) newErrors.project_id = 'Please select a project';
    if (!formData.amount || parseFloat(formData.amount) <= 0) newErrors.amount = 'Valid investment amount is required';
    if (!formData.investment_date) newErrors.investment_date = 'Investment date is required';
    
    if (formData.expected_return && parseFloat(formData.expected_return) < 0) {
      newErrors.expected_return = 'Expected return cannot be negative';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    try {
      const investmentData = {
        ...formData,
        amount: parseFloat(formData.amount),
        expected_return: formData.expected_return ? parseFloat(formData.expected_return) : null,
        investment_date: new Date(formData.investment_date).toISOString()
      };
      
      await addInvestment(investmentData);
      handleClose();
    } catch (error) {
      console.error('Failed to add investment:', error);
    }
  };

  const handleClose = () => {
    setFormData({
      project_id: '',
      amount: '',
      investment_date: new Date().toISOString().split('T')[0],
      expected_return: '',
      notes: '',
      reward_tier: ''
    });
    setErrors({});
    onClose();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const selectedProject = projects.find(p => p.id === formData.project_id);
  const calculatedROI = formData.amount && formData.expected_return 
    ? (((parseFloat(formData.expected_return) - parseFloat(formData.amount)) / parseFloat(formData.amount)) * 100).toFixed(1)
    : null;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
      <div className="relative p-5 border w-11/12 md:w-2/3 lg:w-1/2 max-w-2xl shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Add New Investment</h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="project_id" className="block text-sm font-medium text-gray-700">Project *</label>
            <select
              id="project_id"
              name="project_id"
              required
              value={formData.project_id}
              onChange={handleInputChange}
              className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                errors.project_id ? 'border-red-300' : 'border-gray-300'
              }`}
            >
              <option value="">Select a project</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name} - {project.creator} ({project.status})
                </option>
              ))}
            </select>
            {errors.project_id && <p className="mt-1 text-sm text-red-600">{errors.project_id}</p>}
            
            {/* Project Info */}
            {selectedProject && (
              <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="text-xs text-blue-800">
                  <div><strong>Category:</strong> {selectedProject.category}</div>
                  <div><strong>Goal:</strong> ${selectedProject.goal_amount?.toLocaleString()}</div>
                  <div><strong>Current:</strong> ${selectedProject.pledged_amount?.toLocaleString()} ({((selectedProject.pledged_amount / selectedProject.goal_amount) * 100).toFixed(1)}%)</div>
                  <div><strong>Risk Level:</strong> <span className={`font-semibold ${
                    selectedProject.risk_level === 'high' ? 'text-red-600' :
                    selectedProject.risk_level === 'medium' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>{selectedProject.risk_level}</span></div>
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="amount" className="block text-sm font-medium text-gray-700">Investment Amount ($) *</label>
              <input
                type="number"
                id="amount"
                name="amount"
                required
                min="0.01"
                step="0.01"
                value={formData.amount}
                onChange={handleInputChange}
                className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.amount ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="100.00"
              />
              {errors.amount && <p className="mt-1 text-sm text-red-600">{errors.amount}</p>}
            </div>
            
            <div>
              <label htmlFor="investment_date" className="block text-sm font-medium text-gray-700">Investment Date *</label>
              <input
                type="date"
                id="investment_date"
                name="investment_date"
                required
                value={formData.investment_date}
                onChange={handleInputChange}
                className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.investment_date ? 'border-red-300' : 'border-gray-300'
                }`}
              />
              {errors.investment_date && <p className="mt-1 text-sm text-red-600">{errors.investment_date}</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="expected_return" className="block text-sm font-medium text-gray-700">Expected Return ($)</label>
              <input
                type="number"
                id="expected_return"
                name="expected_return"
                min="0"
                step="0.01"
                value={formData.expected_return}
                onChange={handleInputChange}
                className={`mt-1 block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 ${
                  errors.expected_return ? 'border-red-300' : 'border-gray-300'
                }`}
                placeholder="150.00"
              />
              {errors.expected_return && <p className="mt-1 text-sm text-red-600">{errors.expected_return}</p>}
              
              {/* ROI Calculator */}
              {calculatedROI && (
                <div className="mt-1 text-sm">
                  <span className="text-gray-600">Calculated ROI: </span>
                  <span className={`font-semibold ${
                    parseFloat(calculatedROI) > 0 ? 'text-green-600' : 
                    parseFloat(calculatedROI) < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {calculatedROI > 0 ? '+' : ''}{calculatedROI}%
                  </span>
                </div>
              )}
            </div>
            
            <div>
              <label htmlFor="reward_tier" className="block text-sm font-medium text-gray-700">Reward Tier</label>
              <input
                type="text"
                id="reward_tier"
                name="reward_tier"
                value={formData.reward_tier}
                onChange={handleInputChange}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Early Bird, Standard, etc."
              />
            </div>
          </div>

          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700">Notes</label>
            <textarea
              id="notes"
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows={3}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Add any notes about this investment..."
            />
            <p className="mt-1 text-sm text-gray-500">{formData.notes.length}/500 characters</p>
          </div>

          {/* Investment Summary */}
          {formData.amount && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Investment Summary</h4>
              <div className="text-sm text-gray-600 space-y-1">
                <div className="flex justify-between">
                  <span>Investment:</span>
                  <span className="font-medium">${parseFloat(formData.amount).toLocaleString()}</span>
                </div>
                {formData.expected_return && (
                  <>
                    <div className="flex justify-between">
                      <span>Expected Return:</span>
                      <span className="font-medium">${parseFloat(formData.expected_return).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Potential Profit:</span>
                      <span className={`font-medium ${
                        (parseFloat(formData.expected_return) - parseFloat(formData.amount)) > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        ${(parseFloat(formData.expected_return) - parseFloat(formData.amount)).toLocaleString()}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading.investments}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading.investments ? 'Adding...' : 'Add Investment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddInvestmentModal;