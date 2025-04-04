// Helper functions to interact with the FastAPI backend

// Simple cache implementation
const apiCache: Record<string, { data: any; timestamp: number }> = {};
const CACHE_DURATION = 30000; // Cache duration in ms (30 seconds)

export async function fetchWithAuth(url: string, options: RequestInit = {}) {
  // In a real app, you would get the token from your auth system
  const token = localStorage.getItem("token")

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

  return fetch(`${apiUrl}${url}`, {
    ...options,
    headers,
  })
}

// Cache-aware fetch function for GET requests
export async function fetchWithCache(url: string, options: RequestInit = {}) {
  // Only cache GET requests
  if (options.method && options.method !== 'GET') {
    return fetchWithAuth(url, options);
  }

  const cacheKey = url;
  const now = Date.now();
  
  // Return cached data if available and not expired
  if (apiCache[cacheKey] && now - apiCache[cacheKey].timestamp < CACHE_DURATION) {
    return {
      ok: true,
      json: () => Promise.resolve(apiCache[cacheKey].data),
      status: 200,
    } as Response;
  }
  
  // Otherwise, fetch new data
  const response = await fetchWithAuth(url, options);
  
  if (response.ok) {
    const data = await response.json();
    // Store in cache
    apiCache[cacheKey] = { 
      data, 
      timestamp: now 
    };
    
    return {
      ok: true,
      json: () => Promise.resolve(data),
      status: response.status,
      text: () => response.text(),
    } as Response;
  }
  
  return response;
}

// Invalidate cache for a specific URL
export function invalidateCache(url: string) {
  delete apiCache[url];
}

// Clear entire cache
export function clearCache() {
  Object.keys(apiCache).forEach(key => delete apiCache[key]);
}

// Auth functions
export async function login(email: string, password: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const response = await fetch(`${apiUrl}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  })

  if (!response.ok) {
    throw new Error("Login failed")
  }

  const data = await response.json()
  localStorage.setItem("token", data.access_token)
  return data
}

export async function register(name: string, email: string, password: string) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
  const response = await fetch(`${apiUrl}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  })

  if (!response.ok) {
    throw new Error("Registration failed")
  }

  return response.json()
}

// Users API
export async function getAllUsers() {
  const response = await fetchWithCache("/users")

  if (!response.ok) {
    throw new Error("Failed to fetch users")
  }

  return response.json()
}

export async function updateRoastConfig(userId: string | number, roastConfig: any) {
  console.log(`Updating roast config for user ${userId} with:`, roastConfig);
  
  try {
    const response = await fetchWithAuth(`/users/${userId}/roast`, {
      method: "POST",
      body: JSON.stringify(roastConfig),
    });
    
    console.log(`Update roast config response status: ${response.status}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Update roast config error: ${errorText}`);
      throw new Error(`Failed to create roast: ${response.status} ${errorText}`);
    }
    
    // Invalidate affected caches
    invalidateCache(`/users/${userId}/roast-config`);
    invalidateCache(`/users/${userId}/all-roasts`);
    
    const data = await response.json();
    console.log(`Update roast config success:`, data);
    return data;
  } catch (error) {
    console.error(`Error in updateRoastConfig:`, error);
    throw error;
  }
}

export async function getAllUserRoasts(userId: string | number) {
  console.log(`API call: getAllUserRoasts for userId: ${userId}`);
  
  try {
    const response = await fetchWithCache(`/users/${userId}/all-roasts`);
    console.log(`API response status: ${response.status}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API error response: ${errorText}`);
      throw new Error(`Failed to fetch user roasts: ${response.status} ${errorText}`);
    }
    
    const data = await response.json();
    console.log(`API response data:`, data);
    return data;
  } catch (error) {
    console.error(`API call error in getAllUserRoasts:`, error);
    throw error;
  }
}

export async function getRoastConfig(userId: string | number) {
  console.log(`Getting roast config for user ${userId}`);
  
  try {
    const response = await fetchWithCache(`/users/${userId}/roast-config`);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Get roast config error: ${errorText}`);
      throw new Error(`Failed to get roast config: ${response.status} ${errorText}`);
    }
    
    const data = await response.json();
    console.log(`Got roast config:`, data);
    return data;
  } catch (error) {
    console.error(`Error in getRoastConfig:`, error);
    throw error;
  }
}

// User profile API
export async function getUserProfile() {
  const response = await fetchWithCache("/users/me")

  if (!response.ok) {
    throw new Error("Failed to fetch user profile")
  }

  return response.json()
}

export async function updateUserProfile(profileData: any) {
  const response = await fetchWithAuth("/users/me", {
    method: "PUT",
    body: JSON.stringify(profileData),
  })

  if (!response.ok) {
    throw new Error("Failed to update profile")
  }

  // Invalidate the profile cache after update
  invalidateCache("/users/me");
  
  return response.json()
}

export async function uploadProfileImage(imageData: string) {
  const response = await fetchWithAuth("/users/me/profile-image", {
    method: "POST",
    body: JSON.stringify({ image_data: imageData }),
  })

  if (!response.ok) {
    throw new Error("Failed to upload profile image")
  }

  // Invalidate the profile cache after updating the image
  invalidateCache("/users/me");
  
  return response.json()
}

