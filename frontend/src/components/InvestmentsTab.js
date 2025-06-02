import React, { useState } from 'react';
import { useInvestments, useAddInvestment, useDeleteInvestment } from '../hooks/useQuery';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const InvestmentsTab = () => {
  const { data: investments, isLoading, error } = useInvestments();
  const addInvestmentMutation = useAddInvestment();
  const deleteInvestmentMutation = useDeleteInvestment();
  
  const [showAddForm, setShowAddForm] = useState(false);
  const [newInvestment, setNewInvestment] = useState({
    project_id: '',
    amount: '',
    investment_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewInvestment(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleAddInvestment = (e) => {
    e.preventDefault();
    
    // Validate form
    if (!newInvestment.project_id || !newInvestment.amount) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    // Convert amount to number
    const investmentData = {
      ...newInvestment,
      amount: parseFloat(newInvestment.amount)
    };
    
    addInvestmentMutation.mutate(investmentData, {
      onSuccess: () => {
        toast.success('Investment added successfully');
        setShowAddForm(false);
        setNewInvestment({
          project_id: '',
          amount: '',
          investment_date: new Date().toISOString().split('T')[0],
          notes: ''
        });
      },
      onError: (error) => {
        toast.error(`Failed to add investment: ${error.message}`);
      }
    });
  };
  
  const handleDeleteInvestment = (id) => {
    if (window.confirm('Are you sure you want to delete this investment?')) {
      deleteInvestmentMutation.mutate(id, {
        onSuccess: () => {
          toast.success('Investment deleted successfully');
        },
        onError: (error) => {
          toast.error(`Failed to delete investment: ${error.message}`);
        }
      });
    }
  };
  
  // Calculate total investment amount
  const totalInvestment = investments?.reduce((sum, inv) => sum + inv.amount, 0) || 0;
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="text-red-500 text-center p-4">
        Error loading investments: {error.message}
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">Your Investments</h2>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Investment
          </button>
        </div>
        
        <div className="mt-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-lg font-medium text-blue-800">
              Total Invested: ${totalInvestment.toString()}
            </p>
          </div>
        </div>
        
        {showAddForm && (
          <div className="mt-6 bg-gray-50 p-4 rounded-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Investment</h3>
            <form onSubmit={handleAddInvestment}>
              <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                <div className="sm:col-span-3">
                  <label htmlFor="project_id" className="block text-sm font-medium text-gray-700">
                    Project ID *
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      name="project_id"
                      id="project_id"
                      value={newInvestment.project_id}
                      onChange={handleInputChange}
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      required
                    />
                  </div>
                </div>
                
                <div className="sm:col-span-3">
                  <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
                    Amount ($) *
                  </label>
                  <div className="mt-1">
                    <input
                      type="number"
                      name="amount"
                      id="amount"
                      value={newInvestment.amount}
                      onChange={handleInputChange}
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      required
                    />
                  </div>
                </div>
                
                <div className="sm:col-span-3">
                  <label htmlFor="investment_date" className="block text-sm font-medium text-gray-700">
                    Investment Date
                  </label>
                  <div className="mt-1">
                    <input
                      type="date"
                      name="investment_date"
                      id="investment_date"
                      value={newInvestment.investment_date}
                      onChange={handleInputChange}
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    />
                  </div>
                </div>
                
                <div className="sm:col-span-6">
                  <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                    Notes
                  </label>
                  <div className="mt-1">
                    <textarea
                      name="notes"
                      id="notes"
                      rows="3"
                      value={newInvestment.notes}
                      onChange={handleInputChange}
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                    ></textarea>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Add Investment
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Project ID
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Amount
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Notes
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {investments?.length > 0 ? (
              investments.map((investment) => (
                <tr key={investment.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {investment.project_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${investment.amount.toString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span>{new Date(investment.investment_date).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {investment.notes}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleDeleteInvestment(investment.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="px-6 py-4 text-center text-sm text-gray-500">
                  No investments found. Add your first investment!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default InvestmentsTab;