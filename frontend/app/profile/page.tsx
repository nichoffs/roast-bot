"use client"

import { useState, useEffect, useRef } from "react"
import Image from "next/image"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import { Camera, Check, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { getUserProfile, updateUserProfile, uploadProfileImage } from "@/lib/api"

const profileFormSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters." }),
  email: z.string().email({ message: "Please enter a valid email address." })
})

type ProfileFormValues = z.infer<typeof profileFormSchema>

export default function ProfilePage() {
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingProfile, setIsLoadingProfile] = useState(true)
  const [isUploadingImage, setIsUploadingImage] = useState(false)
  const [profileImage, setProfileImage] = useState<string>("/placeholder.svg?height=160&width=160")
  const [feedback, setFeedback] = useState({ message: "", isError: false, show: false })
  const fileInputRef = useRef<HTMLInputElement>(null)

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: {
      name: "",
      email: ""
    }
  })

  useEffect(() => {
    async function loadProfile() {
      try {
        setIsLoadingProfile(true)
        const userData = await getUserProfile()
        form.reset({
          name: userData.name,
          email: userData.email
        })
        
        // Set profile image if available
        if (userData.image) {
          // Image URL is now absolute from backend
          setProfileImage(userData.image);
        }
      } catch (error) {
        console.error("Error loading profile:", error)
        showFeedback("Failed to load profile data", true)
      } finally {
        setIsLoadingProfile(false)
      }
    }

    loadProfile()
  }, [form])

  const showFeedback = (message: string, isError: boolean) => {
    setFeedback({ message, isError, show: true });
    setTimeout(() => setFeedback(prev => ({ ...prev, show: false })), 3000);
  };

  async function onSubmit(data: ProfileFormValues) {
    setIsLoading(true)
    try {
      await updateUserProfile(data)
      showFeedback("Profile updated successfully", false)
    } catch (error) {
      console.error("Error updating profile:", error)
      showFeedback("Failed to update profile", true)
    } finally {
      setIsLoading(false)
    }
  }

  const handleImageClick = () => {
    fileInputRef.current?.click()
  }

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploadingImage(true)
    try {
      // Convert image to base64
      const reader = new FileReader()
      
      reader.onload = async (event) => {
        if (event.target?.result) {
          const base64Image = event.target.result as string
          
          // Upload image to server
          const response = await uploadProfileImage(base64Image)
          
          // Update local state with new image URL from server
          setProfileImage(response.image_url)
          
          showFeedback("Profile image updated successfully", false)
        }
        setIsUploadingImage(false)
      }
      
      reader.onerror = () => {
        showFeedback("Failed to read image file", true)
        setIsUploadingImage(false)
      }
      
      reader.readAsDataURL(file)
    } catch (error) {
      console.error("Error uploading image:", error)
      showFeedback("Failed to upload image", true)
      setIsUploadingImage(false)
    }
  }

  if (isLoadingProfile) {
    return <div className="flex justify-center py-12">Loading profile...</div>
  }

  return (
    <div className="space-y-6">
      {feedback.show && (
        <div className={`p-3 rounded fixed top-4 right-4 z-50 transition-opacity ${feedback.isError ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
          {feedback.message}
        </div>
      )}
      
      <div>
        <h1 className="text-3xl font-bold">Profile Settings</h1>
        <p className="text-muted-foreground">Manage your account settings and preferences</p>
      </div>

      <div className="grid gap-6 md:grid-cols-[1fr_2fr]">
        <Card>
          <CardHeader>
            <CardTitle>Your Photo</CardTitle>
            <CardDescription>This is your public profile image</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <div className="relative h-40 w-40 rounded-full overflow-hidden mb-4">
              <Image src={profileImage} alt="Profile" fill className="object-cover" />
              <div 
                className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity cursor-pointer"
                onClick={handleImageClick}
              >
                {isUploadingImage ? (
                  <Loader2 className="h-6 w-6 text-white animate-spin" />
                ) : (
                  <Button variant="secondary" size="sm">
                    <Camera className="mr-2 h-4 w-4" />
                    Change
                  </Button>
                )}
              </div>
            </div>
            <input 
              type="file" 
              accept="image/*" 
              className="hidden" 
              ref={fileInputRef} 
              onChange={handleImageUpload}
            />
          </CardContent>
          <CardFooter className="flex justify-center">
            <div className="text-sm text-muted-foreground">JPG, GIF or PNG. Max 2MB.</div>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
            <CardDescription>Update your account information</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Name</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormDescription>This is your public display name.</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormDescription>Your account email address.</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Separator />

                <Button type="submit" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Check className="mr-2 h-4 w-4" />
                      Save Changes
                    </>
                  )}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

