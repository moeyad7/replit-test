/**
 * Proxy module to redirect API calls to the Python backend
 */

// The base URL of the Python backend
const PYTHON_BACKEND_URL = 'http://localhost:5000';

/**
 * Function to proxy API requests to the Python backend
 */
export async function pythonApiRequest(
  method: string,
  endpoint: string,
  data?: unknown
): Promise<Response> {
  // Construct the full URL to the Python backend
  const url = `${PYTHON_BACKEND_URL}${endpoint}`;
  
  console.log(`Proxying ${method} request to Python backend: ${url}`);
  
  // Make the API request to the Python backend
  const response = await fetch(url, {
    method,
    headers: data ? { 'Content-Type': 'application/json' } : {},
    body: data ? JSON.stringify(data) : undefined,
  });
  
  // Check if the response is ok
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Error from Python backend: ${response.status} - ${errorText}`);
  }
  
  return response;
}