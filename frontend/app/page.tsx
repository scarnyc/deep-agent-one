export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Deep Agent AGI</h1>
        <p className="text-muted-foreground mb-8">
          General-purpose deep agent framework
        </p>
        <a
          href="/chat"
          className="inline-flex items-center justify-center rounded-md bg-primary px-8 py-3 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
        >
          Start Chat
        </a>
      </div>
    </main>
  );
}
