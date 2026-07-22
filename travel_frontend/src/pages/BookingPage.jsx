import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { recommendationAPI } from '../services/api';

export default function BookingPage() {
  const { packageId } = useParams();
  const navigate = useNavigate();

  const [pkg, setPkg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [bookingId, setBookingId] = useState(null);
  const [formData, setFormData] = useState({
    full_name: '',
    contact_no: '',
    email: '',
    payment_method: 'Cash',
  });

  useEffect(() => {
    const fetchPackage = async () => {
      try {
        const response = await recommendationAPI.getRecommendedPackage(packageId);
        setPkg(response.data || null);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load package details.');
      } finally {
        setLoading(false);
      }
    };

    fetchPackage();
  }, [packageId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const isValidNepalPhone = (value) => {
    const cleaned = String(value || '').replace(/\s+/g, '').trim();
    return /^(?:\+977|977)?9[78][0-9]{8}$/.test(cleaned);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!isValidNepalPhone(formData.contact_no)) {
      setError('Please enter a valid Nepal mobile number (e.g. 98xxxxxxxx or +97798xxxxxxxx).');
      return;
    }

    setSubmitting(true);

    try {
      const response = await recommendationAPI.createBooking({
        package: Number(packageId),
        ...formData,
      });

      setBookingId(response.data?.booking?.id);

      if (formData.payment_method === 'Online Payment') {
        // Initiate online payment (hosted checkout)
        initiateKhaltiPayment(response.data?.booking?.id);
      } else {
        // On Arrival - just confirm
        setSuccess('Booking request submitted successfully. You will be called for confirmation.');
        setTimeout(() => {
          navigate('/home');
        }, 2000);
      }
    } catch (err) {
      const apiErrors = err.response?.data;
      const message = apiErrors?.error ||
        (typeof apiErrors === 'object'
          ? Object.values(apiErrors).flat(Infinity).join(' ')
          : err.message || 'Booking failed. Please try again.');
      setError(String(message));
    } finally {
      setSubmitting(false);
    }
  };

  const initiateKhaltiPayment = async (newBookingId) => {
    try {
      setSubmitting(true);
      const response = await recommendationAPI.initiatePayment(newBookingId);
      const paymentData = response.data;

      console.log('Payment data received:', paymentData);

      // Backend will return a hosted payment URL (Stripe Checkout) — redirect the browser there
      if (paymentData.checkout_url) {
        window.location.href = paymentData.checkout_url;
        return;
      }

      // Backwards compatibility: some responses may include `session_url` or `url`
      if (paymentData.session_url) {
        window.location.href = paymentData.session_url;
        return;
      }

      if (paymentData.url) {
        window.location.href = paymentData.url;
        return;
      }

      // If still no URL, show the provider response for debugging
      console.error('No redirect URL returned from server:', paymentData);
      setError('Failed to start payment: no redirect URL returned by server.');
      setSubmitting(false);
    } catch (err) {
      console.error('Payment initiation error:', err);
      const serverData = err.response?.data;
      const serverMsg = serverData ? (serverData.error || JSON.stringify(serverData)) : err.message;
      setError('Failed to initiate payment. ' + String(serverMsg));
      setSubmitting(false);
    }
  };

  const handlePaymentSuccess = async (bookingIdFromPayment, payload) => {
    try {
      // Verify payment with backend
      const verifyResponse = await recommendationAPI.verifyPayment(
        payload.pidx,
        payload.transaction_id,
        bookingIdFromPayment,
        'Completed'
      );

      if (verifyResponse.status === 200) {
        setSuccess('Payment successful! Your booking is confirmed.');
        setTimeout(() => {
          navigate(`/payment-success/${bookingIdFromPayment}`);
        }, 1500);
      }
    } catch (err) {
      setError('Payment verification failed. Please contact support.');
    }
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-gray-700">Loading booking details...</div>;
  }

  if (!pkg) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-700 mb-4">Package not found.</p>
          <button onClick={() => navigate('/home')} className="px-4 py-2 bg-blue-600 text-white rounded">Back to Home</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="grid md:grid-cols-2">
          <div className="p-8 bg-blue-50">
            <button type="button" onClick={() => navigate('/home')} className="text-blue-700 font-semibold mb-4">← Back</button>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Booking Request</h1>
            <p className="text-sm text-gray-600 mb-6">Complete the form below to request a booking for your selected package.</p>

            <div className="rounded-lg bg-white p-4 shadow-sm border border-blue-100">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">{pkg.name}</h2>
              <p className="text-sm text-gray-600 mb-1">{pkg.start_location} → {pkg.end_location}</p>
              <p className="text-sm text-gray-600">Duration: {pkg.days} days</p>
              <p className="text-sm text-green-700 font-semibold mt-2">Price: NPR {Number(pkg.budget || 0).toLocaleString()}</p>
            </div>
          </div>

          <div className="p-8">
            {error && (
              <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{error}</div>
            )}

            {success && (
              <div className="mb-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">{success}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input type="text" name="full_name" value={formData.full_name} onChange={handleChange} required className="w-full px-4 py-2 border rounded-lg" placeholder="Enter full name" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contact No</label>
                <input
                  type="text"
                  name="contact_no"
                  value={formData.contact_no}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-2 border rounded-lg"
                  placeholder="e.g. 98xxxxxxxx or +97798xxxxxxxx"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} required className="w-full px-4 py-2 border rounded-lg" placeholder="Enter email" />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                <select
                  name="payment_method"
                  value={formData.payment_method}
                  onChange={handleChange}
                  className="w-full px-4 py-2 border rounded-lg bg-white"
                >
                  <option value="Cash">Cash</option>
                  <option value="Online Payment">Online Payment (Card)</option>
                </select>
              </div>

                              {formData.payment_method === 'Online Payment' && (
                <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 text-sm text-orange-800">
                  <strong>Online Payment (Card)</strong>
                  <p className="mt-2 text-xs">You will be redirected to a secure checkout. Payment amount: <strong>NPR {Number(pkg.budget || 0).toLocaleString()}</strong></p>
                </div>
              )}

              <button type="submit" disabled={submitting} className="w-full bg-blue-600 text-white font-semibold py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50">
                {submitting ? 'Processing...' : formData.payment_method === 'Online Payment' ? 'Continue to Payment' : 'Submit Booking Request'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
