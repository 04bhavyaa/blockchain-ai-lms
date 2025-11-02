// API Client with all endpoints

class APIClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async request(method, endpoint, data = null) {
    const url = `${this.baseURL}${endpoint}`;
    const token = getToken();
    
    const options = {
      method,
      headers: {
        ...API_CONFIG.HEADERS,
        ...(token && { 'Authorization': `Bearer ${token}` })
      }
    };

    if (data) {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || result.message || 'API Error');
      }

      return result;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // AUTH ENDPOINTS
  async login(email, password) {
  const response = await this.request('POST', '/auth/login/', { email, password });
  
  // Save token
  if (response.access) {
    setToken(response.access);
  }
  
  // Save user data
  if (response.user) {
    setUser(response.user);
  }
  
  return response;
}

  async register(email, username, password) {
    return this.request('POST', '/auth/register/', { email, username, password });
  }

  async logout() {
    return this.request('POST', '/auth/logout/');
  }

  async getProfile() {
    return this.request('GET', '/auth/profile/');
  }

  async updateProfile(data) {
    return this.request('PUT', '/auth/profile/update/', data);
  }

  // COURSES ENDPOINTS
  async getCourses(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request('GET', `/courses/?${query}`);
  }

  async getCourseDetail(courseId) {
    return this.request('GET', `/courses/${courseId}/`);
  }

  async enrollCourse(courseId) {
    return this.request('POST', `/courses/${courseId}/enroll/`);
  }

  async unenrollCourse(courseId) {
    return this.request('POST', `/courses/${courseId}/unenroll/`);
  }

  async rateCourse(courseId, rating) {
    return this.request('POST', `/courses/${courseId}/rate/`, { rating });
  }

  async bookmarkCourse(courseId) {
    return this.request('POST', `/courses/${courseId}/bookmark/`);
  }

  // PROGRESS ENDPOINTS
  async getDashboard() {
    return this.request('GET', '/progress/courses/dashboard/');
  }

  async getCourseProgress(courseId) {
    return this.request('GET', `/progress/courses/${courseId}/`);
  }

  async submitQuiz(quizId, answers) {
    return this.request('POST', `/progress/quizzes/${quizId}/submit/`, { answers });
  }

  async getQuizAttempts() {
    return this.request('GET', '/progress/quiz-attempts/');
  }

  // PAYMENT ENDPOINTS
  async getPackages() {
    return this.request('GET', '/payment/packages/');
  }

  async getPurchases() {
    return this.request('GET', '/payment/purchases/');
  }

  async getInvoices() {
    return this.request('GET', '/payment/invoices/');
  }

  async createPaymentIntent(packageId) {
    return this.request('POST', '/payment/create-payment-intent/', { package_id: packageId });
  }

  async confirmPayment(intentId) {
    return this.request('POST', '/payment/confirm-payment/', { payment_intent_id: intentId });
  }

  // BLOCKCHAIN ENDPOINTS
  async getCertificates() {
    return this.request('GET', '/blockchain/certificates/');
  }

  async mintCertificate(courseId) {
    return this.request('POST', '/blockchain/mint-certificate/', { course_id: courseId });
  }

  async verifyCertificate(certificateId) {
    return this.request('GET', `/blockchain/certificates/${certificateId}/`);
  }

  // RECOMMENDATIONS ENDPOINTS
  async getSuggestions() {
    return this.request('GET', '/recommendations/suggestions/');
  }

  async getTrendingCourses() {
    return this.request('GET', '/recommendations/trending/');
  }
}

const api = new APIClient(API_CONFIG.BASE_URL);
console.log('✅ API Client loaded');