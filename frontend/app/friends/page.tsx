"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { User, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { getAllUsers, updateRoastConfig, getAllUserRoasts, getRoastConfig } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

interface UserRoast {
  user_id: string;
  user_name: string;
  topics: string[];
  style: string;
}

export default function UsersPage() {
  const [users, setUsers] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [feedback, setFeedback] = useState({ message: "", isError: false, show: false })

  useEffect(() => {
    async function loadUsers() {
      try {
        const data = await getAllUsers()
        setUsers(data)
      } catch (error) {
        console.error("Error loading users:", error)
        showFeedback("Failed to load users data", true)
      } finally {
        setIsLoading(false)
      }
    }

    loadUsers()
  }, [])

  const showFeedback = (message: string, isError: boolean) => {
    setFeedback({ message, isError, show: true })
    setTimeout(() => setFeedback(prev => ({ ...prev, show: false })), 3000)
  }

  if (isLoading) {
    return <div className="flex justify-center py-12">Loading users...</div>
  }

  return (
    <div className="space-y-6">
      {feedback.show && (
        <div className={`p-3 rounded fixed top-4 right-4 z-50 transition-opacity ${feedback.isError ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
          {feedback.message}
        </div>
      )}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">People on the Platform</h1>
        </div>
        <p className="text-muted-foreground">View and roast other people on the platform</p>
      </div>

      {users.length > 0 ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {users.map((user) => (
            <UserCard key={user.id} user={user} onShowFeedback={showFeedback} />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border p-8 text-center">
          <User className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-medium">No users found</h3>
          <p className="mt-2 text-sm text-muted-foreground">Be the first to join!</p>
        </div>
      )}
    </div>
  )
}

interface UserCardProps {
  user: {
    id: string | number;
    name: string;
    image: string;
    roastCount: number;
  }
  onShowFeedback: (message: string, isError: boolean) => void;
}

function UserCard({ user, onShowFeedback }: UserCardProps) {
  const [openRoastDialog, setOpenRoastDialog] = useState(false)
  const [openViewRoastsDialog, setOpenViewRoastsDialog] = useState(false)
  const [roastTopics, setRoastTopics] = useState({
    topic1: "",
    topic2: "",
    topic3: "",
    style: "Funny but not too mean",
  })
  const [userRoasts, setUserRoasts] = useState<UserRoast[]>([])
  const [isLoadingRoasts, setIsLoadingRoasts] = useState(false)
  const [isLoadingConfig, setIsLoadingConfig] = useState(false)

  const loadRoastConfig = async () => {
    try {
      setIsLoadingConfig(true);
      const config = await getRoastConfig(user.id);
      console.log("Loaded existing roast config:", config);
      
      setRoastTopics({
        topic1: config.topics[0] || "",
        topic2: config.topics[1] || "",
        topic3: config.topics[2] || "",
        style: config.style || "Funny but not too mean",
      });
    } catch (error) {
      console.error("Error loading roast config:", error);
    } finally {
      setIsLoadingConfig(false);
    }
  };

  useEffect(() => {
    if (openRoastDialog) {
      loadRoastConfig();
    }
  }, [openRoastDialog, user.id]);

  const handleSaveRoastConfig = async () => {
    try {
      console.log("Saving roast config for user ID:", user.id, "Type:", typeof user.id);
      console.log("Roast topics to save:", {
        topics: [roastTopics.topic1, roastTopics.topic2, roastTopics.topic3].filter(Boolean),
        style: roastTopics.style,
      });
      
      await updateRoastConfig(user.id, {
        topics: [roastTopics.topic1, roastTopics.topic2, roastTopics.topic3].filter(Boolean),
        style: roastTopics.style,
      });

      setOpenRoastDialog(false);
      
      // Refresh the roasts view if it's open
      if (openViewRoastsDialog) {
        handleViewRoasts();
      }
      
      onShowFeedback("Roast configuration saved successfully", false);
    } catch (error) {
      console.error("Error saving roast config:", error);
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      onShowFeedback(`Failed to save roast configuration: ${errorMessage}`, true);
    }
  }
  
  const handleViewRoasts = async () => {
    setIsLoadingRoasts(true)
    try {
      console.log(`Fetching roasts for user ID: ${user.id}, type: ${typeof user.id}`);
      const roasts = await getAllUserRoasts(user.id)
      console.log("Received roasts:", roasts);
      setUserRoasts(roasts)
      setOpenViewRoastsDialog(true)
    } catch (error) {
      console.error("Error fetching roasts:", error)
      // Show more details about the error
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      onShowFeedback(`Failed to load roasts: ${errorMessage}`, true)
    } finally {
      setIsLoadingRoasts(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between">
          <CardTitle>{user.name}</CardTitle>
        </div>
        <CardDescription>Roasted {user.roastCount} times</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <div className="relative h-24 w-24 rounded-full overflow-hidden mb-4">
          <Image src={user.image || "/placeholder-user.jpg"} alt={user.name} fill className="object-cover" />
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Dialog open={openRoastDialog} onOpenChange={setOpenRoastDialog}>
          <DialogTrigger asChild>
            <Button variant="outline">Create Roast</Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create Roast for {user.name}</DialogTitle>
              <DialogDescription>
                Set custom roast topics for this person. The AI will use these to generate a personalized roast.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="roast-topic-1">Roast Topic 1</Label>
                <Input
                  id="roast-topic-1"
                  placeholder="e.g., Their fashion sense"
                  value={roastTopics.topic1}
                  onChange={(e) => setRoastTopics({ ...roastTopics, topic1: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="roast-topic-2">Roast Topic 2</Label>
                <Input
                  id="roast-topic-2"
                  placeholder="e.g., Their cooking skills"
                  value={roastTopics.topic2}
                  onChange={(e) => setRoastTopics({ ...roastTopics, topic2: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="roast-topic-3">Roast Topic 3</Label>
                <Input
                  id="roast-topic-3"
                  placeholder="e.g., Their gaming abilities"
                  value={roastTopics.topic3}
                  onChange={(e) => setRoastTopics({ ...roastTopics, topic3: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="roast-style">Roast Style</Label>
                <Input
                  id="roast-style"
                  placeholder="e.g., Sarcastic, Silly, Exaggerated"
                  value={roastTopics.style}
                  onChange={(e) => setRoastTopics({ ...roastTopics, style: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleSaveRoastConfig}>Create Roast</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        
        <Button 
          variant="secondary" 
          onClick={handleViewRoasts}
          disabled={isLoadingRoasts}
        >
          <MessageSquare className="mr-2 h-4 w-4" />
          {isLoadingRoasts ? "Loading..." : "View Roasts"}
        </Button>
        
        <Dialog open={openViewRoastsDialog} onOpenChange={setOpenViewRoastsDialog}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Roasts for {user.name}</DialogTitle>
              <DialogDescription>
                See how others have set up roasts for this person
              </DialogDescription>
            </DialogHeader>
            
            <div className="py-4 max-h-[60vh] overflow-y-auto">
              {userRoasts.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No roasts created for this person yet
                </div>
              ) : (
                <div className="space-y-4">
                  {userRoasts.map((roast, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="font-medium mb-2">By {roast.user_name}</div>
                      <div className="space-y-2">
                        <div>
                          <span className="text-muted-foreground text-sm">Topics:</span>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {roast.topics.length > 0 ? (
                              roast.topics.map((topic, i) => (
                                <Badge key={i} variant="secondary">{topic}</Badge>
                              ))
                            ) : (
                              <span className="text-muted-foreground text-sm">No topics specified</span>
                            )}
                          </div>
                        </div>
                        <Separator />
                        <div>
                          <span className="text-muted-foreground text-sm">Style:</span>
                          <div className="mt-1">{roast.style}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <DialogFooter>
              <Button onClick={() => setOpenViewRoastsDialog(false)}>Close</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  )
}
