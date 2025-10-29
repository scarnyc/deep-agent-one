/**
 * Simple test to verify Jest configuration is working
 */

describe('Jest Configuration', () => {
  it('should run tests successfully', () => {
    expect(true).toBe(true)
  })

  it('should have access to environment variables', () => {
    expect(process.env.NEXT_PUBLIC_API_URL).toBe('http://localhost:8000')
    expect(process.env.NEXT_PUBLIC_ENV).toBe('test')
    expect(process.env.NODE_ENV).toBe('test')
  })

  it('should have crypto.randomUUID available', () => {
    expect(crypto.randomUUID).toBeDefined()
    const uuid = crypto.randomUUID()
    expect(uuid).toBeDefined()
    expect(typeof uuid).toBe('string')
    // UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    expect(uuid).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
  })

  it('should have window.matchMedia mocked', () => {
    expect(window.matchMedia).toBeDefined()
    const mediaQuery = window.matchMedia('(min-width: 768px)')
    expect(mediaQuery).toBeDefined()
    expect(mediaQuery.matches).toBe(false)
  })
})
