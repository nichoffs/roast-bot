import * as React from "react"

export interface ToastProps {
  title?: string
  description?: string
  variant?: "default" | "destructive"
}

interface ToastContextType {
  toast: (props: ToastProps) => void
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Array<ToastProps & { id: number }>>([])
  const toastIdRef = React.useRef(0)

  const toast = React.useCallback((props: ToastProps) => {
    const id = toastIdRef.current++
    setToasts((prevToasts) => [...prevToasts, { ...props, id }])
    
    // Auto-hide toast after 3 seconds
    setTimeout(() => {
      setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id))
    }, 3000)
  }, [])

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`p-4 rounded-md shadow-md ${
              toast.variant === "destructive" 
                ? "bg-red-100 text-red-800" 
                : "bg-green-100 text-green-800"
            }`}
          >
            {toast.title && <div className="font-medium">{toast.title}</div>}
            {toast.description && <div className="text-sm">{toast.description}</div>}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = React.useContext(ToastContext)
  if (context === undefined) {
    throw new Error("useToast must be used within a ToastProvider")
  }
  return context
}

// Simpler alternative export to maintain compatibility
export const toast = {
  // Simpler version for direct use in components
  // This won't actually show toasts, but will prevent crashes when imported
  title: "",
  description: "",
  variant: "default" as const,
} 