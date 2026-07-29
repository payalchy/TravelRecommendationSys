import React from 'react';
import { Link } from 'react-router-dom';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div>
            <p className="text-base font-semibold text-blue-700">Travel Recommendation System</p>
          </div>
        </div>

        <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
          <Link to="#about" className="transition hover:text-blue-700">About</Link>
          <Link to="#how-it-works" className="transition hover:text-blue-700">How It Works</Link>
          <Link
            to="/register"
            className="rounded-full bg-blue-600 px-5 py-2 text-white shadow-sm shadow-blue-500/20 transition hover:bg-blue-700"
          >
            Register
          </Link>
        </nav>
      </header>

      <main className="mx-auto grid max-w-7xl gap-12 px-6 pb-16 lg:grid-cols-[1.25fr_0.9fr] lg:px-8 lg:pb-24">
        <section className="flex flex-col justify-center gap-8 py-8 lg:py-16">
          <div className="inline-flex items-center gap-2 rounded-full bg-blue-100 px-4 py-2 text-sm font-semibold text-blue-700 shadow-sm">
            Personalized Travel Recommendations
          </div>

          <div className="space-y-6">
            <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
              Discover your perfect destination.
            </h1>
            <p className="max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
              Get personalized travel recommendations based on your preferences and explore the available package.
            </p>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60">
            <div className="flex items-start gap-4">
              <div>
                <p className="text-sm font-semibold text-slate-900">You need to register and fill the form to get destination recommendations.</p>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Sign up now to unlock personalized destination suggestions tailored to your travel preferences.
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
            <Link
              to="/register"
              className="inline-flex items-center justify-center rounded-full bg-blue-600 px-8 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/30 transition hover:bg-blue-700"
            >
              Register Now
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center justify-center rounded-full border border-slate-200 bg-white px-8 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
            >
              Login
            </Link>
          </div>
        </section>

        <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-slate-100 via-white to-slate-50 p-8 shadow-xl shadow-slate-300/40">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.18),_transparent_30%)]" />
          <div className="relative grid h-full gap-6">
            <div className="rounded-[1.75rem] bg-white/90 p-8 shadow-[0_24px_50px_-30px_rgba(15,23,42,0.55)] backdrop-blur-sm">
              <div className="aspect-[4/3] overflow-hidden rounded-3xl bg-slate-200">
                <div className="flex h-full items-end justify-end bg-[url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1120&q=80')] bg-cover bg-center" />
              </div>
            </div>
            <div className="rounded-3xl bg-slate-900/5 p-6 text-slate-700 ring-1 ring-slate-200/80">
              <div className="space-y-4">
                <p className="text-sm uppercase tracking-[0.24em] text-blue-700">Unlock your perfect destinations</p>
                <h2 className="text-2xl font-semibold text-slate-900">Register and complete the form to get recommendations tailored just for you.</h2>
                <p className="text-sm leading-7 text-slate-600">Our system learns your interests so you can find destinations with confidence.</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <section id="how-it-works" className="mx-auto max-w-7xl px-6 pb-20 lg:px-8">
        <div className="rounded-[2rem] bg-white py-14 px-8 shadow-lg shadow-slate-200/60 sm:px-12">
          <div className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-700">How It Works</p>
            <h2 className="mt-4 text-3xl font-semibold text-slate-900 sm:text-4xl">Simple steps to your next adventure</h2>
            <p className="mt-4 text-base leading-8 text-slate-600">Register, tell us your preferences, and receive destination recommendations matching your preferences.</p>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-8 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-blue-700 shadow-sm">
                1
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Register</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">Create your account to get started.</p>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-8 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-blue-700 shadow-sm">
                2
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Fill the form</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">Tell us about your preferences.</p>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-slate-50 p-8 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-blue-700 shadow-sm">
                3
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Get recommendations</h3>
              <p className="mt-3 text-sm leading-6 text-slate-600">Receive personalized destination suggestions just for you.</p>
            </div>
          </div>
        </div>
      </section>

      <footer id="contact" className="mx-auto max-w-7xl px-6 pb-10 text-sm text-slate-500 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 border-t border-slate-200 pt-6 sm:flex-row">
          <p>© 2026 Travel Recommendation System. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <Link to="#" className="transition hover:text-slate-900">Privacy Policy</Link>
            <Link to="#" className="transition hover:text-slate-900">Terms of Use</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
