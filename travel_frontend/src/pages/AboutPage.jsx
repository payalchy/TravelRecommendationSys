import React from 'react';
import { Link } from 'react-router-dom';
import boudhaImage from '../assets/images/boudha.jpg';
import missionImage from '../assets/images/our.jpg';
import youImage from '../assets/images/you.jpg';
import nepalImage from '../assets/images/nepal.jpg';
import smartImage from '../assets/images/smart.jpg';
import travelCardImage from '../assets/images/travel.jpg';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="absolute inset-x-0 top-0 z-20 mx-auto flex max-w-7xl items-center justify-between px-6 py-5 lg:px-8">
        <div>
          <p className="text-lg font-extrabold uppercase tracking-[0.3em] text-blue-200 drop-shadow-lg sm:text-2xl lg:text-3xl">
            Travel Recommendation System
          </p>
        </div>
        <nav className="hidden items-center gap-8 text-sm font-medium text-white md:flex">
          <Link to="/" className="transition hover:text-blue-200">Home</Link>
          <Link to="/about" className="transition border-b-2 border-white pb-1 text-white">About</Link>
          <Link
            to="/register"
            className="rounded-full bg-blue-600 px-5 py-2 text-white shadow-sm shadow-blue-500/20 transition hover:bg-blue-700"
          >
            Register
          </Link>
        </nav>
      </header>

      <main className="relative">
        <section className="relative">
          <img
            src={boudhaImage}
            alt="Boudha"
            className="h-[520px] w-full object-cover"
          />
          <div className="absolute inset-0 bg-slate-950/30" />
          <div className="absolute inset-0 mx-auto flex max-w-7xl items-center px-6 lg:px-8">
            <div className="max-w-3xl px-4 py-10 sm:px-6">
              <p className="text-sm uppercase tracking-[0.3em] text-blue-100">About Us</p>
              <h1 className="mt-6 text-4xl font-semibold text-white sm:text-5xl">About Our Travel Recommendation System</h1>
              <p className="mt-6 text-base leading-8 text-slate-100/90 sm:text-lg">
                Discover amazing destinations across Nepal with personalized recommendations based on your budget, travel duration, preferred season, travel style, location, and interests.
              </p>
              <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center">
                <Link
                  to="/register"
                  className="inline-flex items-center justify-center rounded-full bg-blue-600 px-8 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-500/30 transition hover:bg-blue-700"
                >
                  Explore Destinations
                </Link>
                <Link
                  to="/"
                  className="inline-flex items-center justify-center rounded-full border border-white/40 bg-white/10 px-8 py-3 text-sm font-semibold text-white transition hover:border-white/60 hover:bg-white/20"
                >
                  Back to Home
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto -mt-6 max-w-7xl px-6 pb-20 lg:px-8">
          <div className="overflow-hidden rounded-[2rem] bg-white p-10 shadow-lg shadow-slate-200/60 sm:p-12">
            <div className="grid gap-10 xl:grid-cols-[1.1fr_0.9fr] xl:items-stretch">
              <div className="space-y-8">
                <div className="max-w-3xl">
                  <h2 className="mt-4 text-3xl font-semibold text-slate-900 sm:text-4xl">Personalized Travel Recommendation System</h2>
                  <p className="mt-4 text-base leading-8 text-slate-600 sm:text-lg">
                   Our Personalized Travel Recommendation System helps you discover the best destinations and travel packages across Nepal based on your budget, travel duration, preferred season, travel style, location, and personal preferences.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <p className="font-semibold text-slate-900">Travel Style</p>
                  </div>
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <p className="font-semibold text-slate-900">Budget & Duration</p>
                  </div>
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <p className="font-semibold text-slate-900">Preferred Season</p>
                  </div>
                   <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <p className="font-semibold text-slate-900">Province Selection</p>
                  </div>
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <p className="font-semibold text-slate-900">Location-Based Suggestions</p>
                  </div>
                  <div className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
                    <p className="font-semibold text-slate-900">Smart Recommendations</p>
                  </div>
                </div>
              </div>

              <div className="relative overflow-hidden rounded-[2rem] h-full xl:self-start">
                <img
                  src={missionImage}
                  alt="Our mission"
                  className="absolute inset-0 h-full w-full object-cover"
                />
              </div>
            </div>
            <div className="mt-12 text-center">
              <p className="text-sm uppercase tracking-[0.3em] font-semibold text-blue-700">Our mission</p>
              <h2 className="mt-4 text-3xl font-semibold text-slate-900 sm:text-4xl">
                Making travel planning simple and personalized
              </h2>
              <p className="mt-4 mx-auto max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
                Save time and effort with smart recommendations that fit your budget and travel duration.
              </p>
            </div>

            <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              <div className="overflow-hidden rounded-3xl bg-slate-50 p-6 shadow-sm ring-1 ring-slate-200 min-h-[220px] transition-transform duration-300 hover:-translate-y-2 hover:shadow-lg hover:shadow-slate-300">
                <img src={youImage} alt="Personalized for You" className="h-32 w-full rounded-3xl object-cover" />
                <p className="mt-5 text-lg font-semibold text-slate-900">Personalized for You</p>
                <p className="mt-3 text-sm leading-7 text-slate-600">Destination ideas matching your preferences and interests.</p>
              </div>
              <div className="overflow-hidden rounded-3xl bg-slate-50 p-6 shadow-sm ring-1 ring-slate-200 min-h-[220px] transition-transform duration-300 hover:-translate-y-2 hover:shadow-lg hover:shadow-slate-300">
                <img src={nepalImage} alt="Explore Nepal" className="h-32 w-full rounded-3xl object-cover" />
                <p className="mt-5 text-lg font-semibold text-slate-900">Explore Nepal</p>
                <p className="mt-3 text-sm leading-7 text-slate-600">Discover incredible places across Nepal from mountains and lakes to culture and wildlife.</p>
              </div>
              <div className="overflow-hidden rounded-3xl bg-slate-50 p-6 shadow-sm ring-1 ring-slate-200 min-h-[220px] transition-transform duration-300 hover:-translate-y-2 hover:shadow-lg hover:shadow-slate-300">
                <img src={smartImage} alt="Smart & Efficient" className="h-32 w-full rounded-3xl object-cover" />
                <p className="mt-5 text-lg font-semibold text-slate-900">Smart & Efficient</p>
                <p className="mt-3 text-sm leading-7 text-slate-600">Save time and effort with smart recommendations that fit your travel plan.</p>
              </div>
              <div className="overflow-hidden rounded-3xl bg-slate-50 p-6 shadow-sm ring-1 ring-slate-200 min-h-[220px] transition-transform duration-300 hover:-translate-y-2 hover:shadow-lg hover:shadow-slate-300">
                <img src={travelCardImage} alt="Travel with Confidence" className="h-32 w-full rounded-3xl object-cover" />
                <p className="mt-5 text-lg font-semibold text-slate-900">Travel with Confidence</p>
                <p className="mt-3 text-sm leading-7 text-slate-600">Book better trips with reliable suggestions and detailed information.</p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
