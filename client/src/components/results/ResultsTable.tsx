import React from "react";
import { DownloadIcon, ArrowLeftIcon, ArrowRightIcon } from "@/components/ui/icons";
import { Button } from "@/components/ui/button";
import { Customer } from "@/lib/types";

interface ResultsTableProps {
  title: string;
  data: Customer[];
  isLoading: boolean;
}

export default function ResultsTable({ title, data, isLoading }: ResultsTableProps) {
  if (!data.length && !isLoading) return null;
  
  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`;
  };
  
  // Handle both camelCase and snake_case property names from API
  const getCustomerName = (customer: any) => {
    const first = customer.firstName || customer.first_name || '';
    const last = customer.lastName || customer.last_name || '';
    return `${first} ${last}`;
  };
  
  const getCustomerEmail = (customer: any) => {
    return customer.email || '';
  };
  
  const getCustomerPoints = (customer: any) => {
    return customer.points || 0;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <h2 className="text-sm font-medium text-gray-800">{title}</h2>
        <div className="flex items-center space-x-2">
          <button className="text-gray-500 hover:text-gray-700 text-sm">
            <DownloadIcon size={16} className="mr-1 inline" /> Export
          </button>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Customer
              </th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Points Earned
              </th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              Array(5).fill(0).map((_, index) => (
                <tr key={index}>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-8 h-8 rounded-full bg-gray-200 animate-pulse" />
                      <div className="ml-3 w-24 h-5 bg-gray-200 animate-pulse rounded" />
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="w-32 h-5 bg-gray-200 animate-pulse rounded" />
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <div className="w-16 h-5 bg-gray-200 animate-pulse rounded ml-auto" />
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right">
                    <div className="w-10 h-5 bg-gray-200 animate-pulse rounded ml-auto" />
                  </td>
                </tr>
              ))
            ) : (
              data.map((customer, index) => (
                <tr key={index}>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className={`w-8 h-8 rounded-full ${index === 0 ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-700'} flex items-center justify-center font-medium text-xs`}>
                        {getInitials(
                          customer.firstName || customer.first_name || '',
                          customer.lastName || customer.last_name || ''
                        )}
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900">{getCustomerName(customer)}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {getCustomerEmail(customer)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 text-right font-medium">
                    {typeof getCustomerPoints(customer) === 'number' ? getCustomerPoints(customer).toLocaleString() : getCustomerPoints(customer)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-right text-sm">
                    <button className="text-primary-600 hover:text-primary-800">View</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {data.length > 0 && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
          <div className="flex-1 flex justify-between sm:hidden">
            <button className="text-sm text-primary-600 hover:text-primary-900 font-medium">
              Previous
            </button>
            <button className="text-sm text-primary-600 hover:text-primary-900 font-medium ml-3">
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing <span className="font-medium">1</span> to <span className="font-medium">{data.length}</span> of <span className="font-medium">{data.length}</span> results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <Button variant="outline" size="sm" className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">
                  <ArrowLeftIcon size={16} />
                </Button>
                <Button variant="outline" size="sm" className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-primary-50 text-sm font-medium text-primary-600 hover:bg-blue-50">
                  1
                </Button>
                <Button variant="outline" size="sm" className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50">
                  <ArrowRightIcon size={16} />
                </Button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
