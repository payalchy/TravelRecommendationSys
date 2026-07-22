import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { recommendationAPI } from '../services/api';

export default function BookingHistoryPage() {
  const navigate = useNavigate();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchBookings = async () => {
      try {
        const response = await recommendationAPI.getUserBookings();
        setBookings(response.data || []);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load booking history.');
      } finally {
        setLoading(false);
      }
    };

    fetchBookings();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Booking History</h1>
            <p className="text-gray-600 mt-1">View the packages you requested and their current booking status.</p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/profile')}
            className="px-4 py-2 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 transition"
          >
            Back to Profile
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-10">
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : bookings.length === 0 ? (
          <div className="rounded-xl bg-white border border-gray-200 p-8 text-center text-gray-600">
            No booking history found yet.
          </div>
        ) : (
          <div className="space-y-4">
            {bookings.map((booking) => (
              <div key={booking.id} className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">Package</p>
                    <p className="text-xl font-semibold text-gray-900">{booking.package_name}</p>
                    <p className="text-sm text-gray-500">Destination: {booking.destination_name || 'N/A'}</p>
                  </div>
                  <div className="rounded-xl bg-gray-50 px-4 py-3 text-sm">
                    <p className="text-gray-500">Status</p>
                    <p className="font-semibold capitalize text-gray-900">{booking.status}</p>
                  </div>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                  <div>
                    <p className="text-xs text-gray-500">Full Name</p>
                    <p className="font-medium text-gray-900">{booking.full_name}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Contact No</p>
                    <p className="font-medium text-gray-900">{booking.contact_no}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Email</p>
                    <p className="font-medium text-gray-900">{booking.email}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Payment</p>
                    <p className="font-medium text-gray-900">{booking.payment_method}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Created At</p>
                    <p className="font-medium text-gray-900">
                      {booking.created_at
                        ? new Intl.DateTimeFormat('en-NP', {
                            timeZone: 'Asia/Kathmandu',
                            dateStyle: 'medium',
                            timeStyle: 'short',
                          }).format(new Date(booking.created_at))
                        : 'N/A'}
                    </p>
                  </div>
                </div>

                {booking.notice && booking.notice !== 'You will receive a call for booking confirmation.' && (
                  <div className="mt-4 rounded-xl bg-yellow-50 border border-yellow-200 px-4 py-3 text-sm text-yellow-800">
                    {booking.notice}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
