export async function fetchSurfaceData(ticker: string) {
  const response = await fetch(`/api/surface/${ticker}`);
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to fetch data');
  }
  return response.json();
}