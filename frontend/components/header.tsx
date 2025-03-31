"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { Menu, X, LogOut, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useMobile } from "@/hooks/use-mobile"
import { getUserProfile } from "@/lib/api"

interface UserProfile {
  id: string
  name: string
  email: string
}

export function Header() {
  const pathname = usePathname()
  const router = useRouter()
  const isMobile = useMobile()
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function loadUserProfile() {
      try {
        const token = localStorage.getItem("token")
        if (!token) {
          setIsLoading(false)
          return
        }
        
        const userData = await getUserProfile()
        setUser(userData)
      } catch (error) {
        console.error("Error loading user profile:", error)
        // Clear token if it's invalid
        localStorage.removeItem("token")
      } finally {
        setIsLoading(false)
      }
    }
    
    loadUserProfile()
  }, [pathname]) // Reload when path changes

  const handleLogout = () => {
    localStorage.removeItem("token")
    setUser(null)
    router.push("/")
  }

  const routes = [
    { name: "Home", path: "/" },
    { name: "People", path: "/friends" },
    { name: "Profile", path: "/profile" },
  ]

  return (
    <header className="border-b sticky top-0 z-50 bg-background">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="font-bold text-2xl">🔥 Roast Bot</span>
          </Link>
        </div>

        {isMobile ? (
          <>
            <Button variant="ghost" size="icon" onClick={() => setIsMenuOpen(!isMenuOpen)} aria-label="Toggle menu">
              {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </Button>
            {isMenuOpen && (
              <div className="fixed inset-0 top-16 z-50 bg-background">
                <nav className="container grid gap-2 p-4">
                  {routes.map((route) => (
                    <Link
                      key={route.path}
                      href={route.path}
                      onClick={() => setIsMenuOpen(false)}
                      className={cn(
                        "flex items-center rounded-md px-4 py-2 text-lg font-medium",
                        pathname === route.path ? "bg-primary text-primary-foreground" : "hover:bg-muted",
                      )}
                    >
                      {route.name}
                    </Link>
                  ))}
                  <div className="mt-4 flex flex-col gap-2">
                    {!isLoading && !user ? (
                      <>
                        <Link href="/login" onClick={() => setIsMenuOpen(false)}>
                          <Button className="w-full" variant="outline">
                            Login
                          </Button>
                        </Link>
                        <Link href="/register" onClick={() => setIsMenuOpen(false)}>
                          <Button className="w-full">Register</Button>
                        </Link>
                      </>
                    ) : (
                      <div className="flex flex-col gap-2">
                        <div className="flex items-center gap-2 px-4 py-2 bg-muted rounded-md">
                          <User size={18} />
                          <span>{user?.name}</span>
                        </div>
                        <Button 
                          variant="outline" 
                          className="w-full" 
                          onClick={() => {
                            handleLogout()
                            setIsMenuOpen(false)
                          }}
                        >
                          <LogOut className="mr-2 h-4 w-4" />
                          Logout
                        </Button>
                      </div>
                    )}
                  </div>
                </nav>
              </div>
            )}
          </>
        ) : (
          <nav className="flex items-center gap-6">
            {routes.map((route) => (
              <Link
                key={route.path}
                href={route.path}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-primary",
                  pathname === route.path ? "text-primary font-semibold" : "text-muted-foreground",
                )}
              >
                {route.name}
              </Link>
            ))}
            <div className="flex items-center gap-2 ml-6">
              {!isLoading && !user ? (
                <>
                  <Link href="/login">
                    <Button variant="outline">Login</Button>
                  </Link>
                  <Link href="/register">
                    <Button>Register</Button>
                  </Link>
                </>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <User size={16} />
                    <span className="font-medium">{user?.name}</span>
                  </div>
                  <Button variant="outline" size="sm" onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </Button>
                </div>
              )}
            </div>
          </nav>
        )}
      </div>
    </header>
  )
}

