"use client"
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="text-2xl font-bold text-red-600">
                UAS EXAM
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href={`${process.env.NEXT_PUBLIC_DJANGO_URL || "http://localhost:8000"}/accounts/login/`}
                className="text-gray-700 hover:text-red-600"
              >
                Login
              </a>
              {/* <a
                href={`${process.env.NEXT_PUBLIC_DJANGO_URL || "http://localhost:8000"}/accounts/signup/`}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
              >
                Sign Up
              </a> */}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-8">International UAS Exam Preparation</h1>
          <p className="text-xl text-gray-600 mb-8">
            Prepare for your International UAS certification with our comprehensive mock exams
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <div className="bg-white border rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Air Law</h3>
              <p className="text-gray-600 mb-4">Aviation regulations and legal requirements</p>
              <a
                href={`${process.env.NEXT_PUBLIC_DJANGO_URL || "http://localhost:8000"}/exams/`}
                className="text-red-600 hover:text-red-700"
              >
                Start Practice →
              </a>
            </div>

            <div className="bg-white border rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Aircraft General Knowledge</h3>
              <p className="text-gray-600 mb-4">Technical knowledge of aircraft systems</p>
              <a
                href={`${process.env.NEXT_PUBLIC_DJANGO_URL || "http://localhost:8000"}/exams/`}
                className="text-red-600 hover:text-red-700"
              >
                Start Practice →
              </a>
            </div>

            <div className="bg-white border rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibent text-gray-900 mb-2">Flight Performance</h3>
              <p className="text-gray-600 mb-4">Performance planning and calculations</p>
              <a
                href={`${process.env.NEXT_PUBLIC_DJANGO_URL || "http://localhost:8000"}/exams/`}
                className="text-red-600 hover:text-red-700"
              >
                Start Practice →
              </a>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Ready to Start?</h2>
            <p className="text-gray-600 mb-4">Access your Django backend to start taking mock exams</p>
            <a
              href={`${process.env.NEXT_PUBLIC_DJANGO_URL || "http://localhost:8000"}`}
              className="inline-block bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700"
            >
              Access Django App
            </a>
          </div>
        </div>
      </main>
    </div>
  )
}
