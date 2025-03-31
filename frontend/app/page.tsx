"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { ArrowRight, Camera, Mic, Brain } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function HomePage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    // Check if token exists in localStorage
    const token = localStorage.getItem("token")
    setIsLoggedIn(!!token)
  }, [])

  return (
    <div className="flex flex-col gap-12 py-8">
      <section className="w-full py-12 md:py-24 lg:py-32">
        <div className="container px-4 md:px-6">
          <div className="flex flex-col items-center gap-4 text-center">
            <h1 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl lg:text-6xl">
              Welcome to Roast Bot
            </h1>
            <p className="max-w-[700px] text-lg text-muted-foreground md:text-xl">
              The AI-powered system that recognizes your friends and delivers personalized roasts
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              {!isLoggedIn ? (
                <Link href="/register">
                  <Button size="lg">
                    Get Started
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              ) : null}
              <Link href="/friends">
                <Button variant={isLoggedIn ? "default" : "outline"} size="lg">
                  View People
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="container">
        <div className="grid gap-8 md:grid-cols-3">
          <Card>
            <CardHeader>
              <Camera className="h-12 w-12 text-primary mb-2" />
              <CardTitle>Facial Recognition</CardTitle>
              <CardDescription>Uses advanced AI to identify your friends from the dataset</CardDescription>
            </CardHeader>
            <CardContent>
              <p>Our system uses a Raspberry Pi camera and DeepFace to recognize your friends in real-time.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Brain className="h-12 w-12 text-primary mb-2" />
              <CardTitle>Custom Roast Generation</CardTitle>
              <CardDescription>Create personalized roast prompts for your friends</CardDescription>
            </CardHeader>
            <CardContent>
              <p>Use our web interface to set up custom roast topics for each person in your friend group.</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <Mic className="h-12 w-12 text-primary mb-2" />
              <CardTitle>Speech Synthesis</CardTitle>
              <CardDescription>Converts roasts to high-quality speech in funny voices</CardDescription>
            </CardHeader>
            <CardContent>
              <p>Leverages ElevenLabs to generate realistic and humorous speech from the AI-written roasts.</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {!isLoggedIn && (
        <section className="container py-12">
          <div className="flex flex-col items-center gap-6 text-center">
            <h2 className="text-3xl font-bold">Ready to set up your roast profiles?</h2>
            <p className="max-w-[600px] text-muted-foreground">
              Create an account to start customizing roast prompts for everyone in your friend group
            </p>
            <Link href="/register">
              <Button size="lg">Sign Up Now</Button>
            </Link>
          </div>
        </section>
      )}
    </div>
  )
}

