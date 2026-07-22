import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useLocation } from 'react-router-dom';
import { recommendationAPI } from '../services/api';

export default function PaymentSuccessPage() {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [resolvedBookingId, setResolvedBookingId] = useState(bookingId || null);
  const [paymentData, setPaymentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const getBookingStatusLabel = (status) => {
    if (!status) return 'Pending';
    const normalized = String(status).trim().toLowerCase();
    if (normalized === 'confirmed') return 'Confirmed';
    if (normalized === 'pending') return 'Pending';
    return status;
  };

  const getStatusClasses = (status) => {
    const normalized = String(status || '').trim().toLowerCase();
    if (normalized === 'confirmed') {
      return 'bg-green-200 text-green-800';
    }
    if (normalized === 'pending') {
      return 'bg-yellow-200 text-yellow-800';
    }
    return 'bg-gray-200 text-gray-800';
  };

  useEffect(() => {
    const run = async () => {
      // If provider redirected back with a token/session, verify first
      const params = new URLSearchParams(location.search);
      const sessionId = params.get('session_id');
      const token = params.get('token') || params.get('pidx') || params.get('payment_token');
      const returnedBookingId = params.get('booking_id') || bookingId;

      try {
        let bookingIdToUse = returnedBookingId;
        let verifyResponse = null;

        if (sessionId) {
          if (returnedBookingId) {
            verifyResponse = await recommendationAPI.verifyPayment(sessionId, returnedBookingId);
          } else {
            verifyResponse = await recommendationAPI.verifyPayment(sessionId);
          }
        } else if (token && returnedBookingId) {
          verifyResponse = await recommendationAPI.verifyPayment(token, returnedBookingId);
        }

        if (verifyResponse?.data?.booking?.id) {
          bookingIdToUse = verifyResponse.data.booking.id;
          setResolvedBookingId(String(bookingIdToUse));
        }

        if (!bookingIdToUse) {
          throw new Error('Missing booking identifier for payment status lookup.');
        }

        const response = await recommendationAPI.getPaymentStatus(bookingIdToUse);
        setPaymentData(response.data);
      } catch (err) {
        setError(err.response?.data?.error || err.message || 'Failed to load payment details.');
      } finally {
        setLoading(false);
      }
    };

    run();
  }, [bookingId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-700">Loading payment details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md text-center">
          <button
            onClick={() => navigate('/home')}
            className="w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Success Card */}
        <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-8 text-center">
            <div className="text-6xl mb-4">✓</div>
            <h1 className="text-4xl font-bold mb-2">Payment Successful!</h1>
            <p className="text-green-100 text-lg">Your booking is now confirmed</p>
          </div>

          {/* Content */}
          <div className="p-8">
            {paymentData && (
              <div className="space-y-6">
                {/* Booking Confirmation */}
                <div className="border-l-4 border-green-500 bg-green-50 p-6 rounded">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">Booking Confirmation</h2>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Booking ID:</span>
                      <span className="font-semibold text-gray-900">#{resolvedBookingId || bookingId || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status:</span>
                      <span className={`inline-block px-3 py-1 rounded-full font-semibold ${getStatusClasses(paymentData.booking_status)}`}>
                        {getBookingStatusLabel(paymentData.booking_status)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Payment Details */}
                <div className="border-l-4 border-blue-500 bg-blue-50 p-6 rounded">
                  <h2 className="text-xl font-bold text-gray-900 mb-4">Payment Details</h2>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Payment Status:</span>
                      <span className="inline-block px-3 py-1 bg-blue-200 text-blue-800 rounded-full font-semibold">
                        {paymentData.payment_status || 'Paid'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Amount Paid:</span>
                      <span className="font-semibold text-gray-900">NPR {paymentData.paid_amount?.toLocaleString() || '0'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Transaction ID:</span>
                      <span className="font-mono text-xs text-gray-800 truncate max-w-xs">
                        {paymentData.transaction_id || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Next Steps */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-3">What's Next?</h2>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li className="flex items-start">
                      <span className="text-amber-600 font-bold mr-3">1.</span>
                      <span>Check your email for the booking confirmation details</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-amber-600 font-bold mr-3">2.</span>
                      <span>Your booking has been confirmed and payment is complete.</span>
                    </li>
                    <li className="flex items-start">
                      <span className="text-amber-600 font-bold mr-3">3.</span>
                      <span>View your booking in "My Bookings" to track the status</span>
                    </li>
                  </ul>
                </div>

                {/* Action Buttons */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                  <button
                    onClick={() => navigate('/booking-history')}
                    className="bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 transition"
                  >
                    View My Bookings
                  </button>
                  <button
                    onClick={() => navigate('/home')}
                    className="border-2 border-blue-600 text-blue-600 font-semibold py-3 rounded-lg hover:bg-blue-50 transition"
                  >
                    Back to Home
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Help Section */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Need Help?</h3>
          <p className="text-gray-600 mb-2">If you have any questions about your booking, please contact us:</p>
          <p className="text-gray-700 font-semibold">📞 +977-1-XXXXXXXX</p>
          <p className="text-gray-700 font-semibold">📧 support@smarttravel.com</p>
        </div>
      </div>
    </div>
  );
}
