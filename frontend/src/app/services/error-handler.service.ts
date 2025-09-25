import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

export interface ErrorMessage {
  message: string;
  type: 'error' | 'warning' | 'info';
  code?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ErrorHandlerService {

  /**
   * Extract user-friendly error message from HTTP error response
   */
  getErrorMessage(error: HttpErrorResponse | any): ErrorMessage {
    // Network/connection errors
    if (error.status === 0) {
      return {
        message: 'Unable to connect to server. Please check your internet connection.',
        type: 'error',
        code: 'NETWORK_ERROR'
      };
    }

    // Backend returns user-friendly messages
    if (error.error?.message) {
      return {
        message: error.error.message,
        type: 'error',
        code: error.error.code || 'BACKEND_ERROR'
      };
    }

    // Legacy backend error field
    if (error.error?.error) {
      return {
        message: error.error.error,
        type: 'error',
        code: 'BACKEND_ERROR'
      };
    }

    // Handle specific HTTP status codes with generic messages
    switch (error.status) {
      case 400:
        return {
          message: 'Invalid request. Please check your input.',
          type: 'error',
          code: 'BAD_REQUEST'
        };
      case 401:
        return {
          message: 'You are not authorized. Please log in again.',
          type: 'error',
          code: 'UNAUTHORIZED'
        };
      case 403:
        return {
          message: 'Access denied. You do not have permission for this action.',
          type: 'error',
          code: 'FORBIDDEN'
        };
      case 404:
        return {
          message: 'The requested resource was not found.',
          type: 'error',
          code: 'NOT_FOUND'
        };
      case 409:
        return {
          message: 'Conflict: The resource already exists or is in use.',
          type: 'warning',
          code: 'CONFLICT'
        };
      case 422:
        return {
          message: 'Validation error. Please check your input.',
          type: 'error',
          code: 'VALIDATION_ERROR'
        };
      case 500:
        return {
          message: 'Server error occurred. Please try again later.',
          type: 'error',
          code: 'SERVER_ERROR'
        };
      case 503:
        return {
          message: 'Service temporarily unavailable. Please try again later.',
          type: 'error',
          code: 'SERVICE_UNAVAILABLE'
        };
      default:
        return {
          message: 'An unexpected error occurred. Please try again.',
          type: 'error',
          code: 'UNKNOWN_ERROR'
        };
    }
  }

  /**
   * Get error message as string (for backward compatibility)
   */
  getErrorMessageString(error: HttpErrorResponse | any): string {
    return this.getErrorMessage(error).message;
  }

  /**
   * Check if error is a specific type
   */
  isErrorType(error: HttpErrorResponse | any, type: string): boolean {
    return this.getErrorMessage(error).code === type;
  }

  /**
   * Check if error is a network error
   */
  isNetworkError(error: HttpErrorResponse | any): boolean {
    return error.status === 0;
  }

  /**
   * Check if error is a validation error
   */
  isValidationError(error: HttpErrorResponse | any): boolean {
    return error.status === 422 || this.isErrorType(error, 'VALIDATION_ERROR');
  }
}
