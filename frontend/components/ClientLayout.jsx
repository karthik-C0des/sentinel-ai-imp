"use client";

import Link from 'next/link';
import Card from '@leafygreen-ui/card';
import { MongoDBLogoMark } from '@leafygreen-ui/logo';
import { palette } from '@/lib/theme';
import { spacing } from '@leafygreen-ui/tokens';
import { H1, Overline, Body } from '@leafygreen-ui/typography';
import Icon from '@leafygreen-ui/icon';
import IconButton from '@leafygreen-ui/icon-button';
import { useState, useEffect, useRef } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useUser } from '@/contexts/UserContext';
import ChatBubble from '@/components/chat/ChatBubble';
import LeafyGreenProvider from '@leafygreen-ui/leafygreen-provider';

const ROUTE_ROLES = [
  { href: '/dashboard', roles: ['risk_analyst'] },
  { href: '/investigations', roles: ['risk_analyst'] },
  { href: '/entities', roles: ['risk_analyst'] },
  { href: '/entity-resolution', roles: ['risk_analyst'] },
  { href: '/transaction-simulator', roles: ['risk_analyst'] },
];

// Suppress LeafyGreen UI Table cellIndex warning caused by outdated component library
// We do this at the module level so it catches errors during hydration, before useEffect runs.
if (typeof window !== 'undefined') {
  const originalError = console.error;
  console.error = (...args) => {
    const msg = typeof args[0] === 'string' ? args[0] : '';
    if (msg.includes('React does not recognize the `%s` prop on a DOM element') && args.includes('cellIndex')) {
      return;
    }
    // Also catch it if it's already interpolated
    if (msg.includes('React does not recognize the `cellIndex` prop on a DOM element')) {
      return;
    }
    // Suppress React 19 element.ref deprecation warning from LeafyGreen UI (library noise, not our code)
    if (msg.includes('Accessing element.ref was removed in React 19')) {
      return;
    }
    originalError(...args);
  };
}

export default function ClientLayout({ children, bianModelUrl }) {
  const [isMenuOpen, setMenuOpen] = useState(false);
  const [isProfileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);
  const { role } = useUser();
  const pathname = usePathname();
  const router = useRouter();

  const isActive = (href) => {
    if (href === '/') return pathname === '/';
    return pathname?.startsWith(href);
  };

  const navLinkStyle = (href) => ({
    color: isActive(href) ? '#12B8B0' : '#0f2942',
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: `${spacing[2]}px ${spacing[3]}px`,
    borderRadius: '4px',
    transition: 'background-color 0.2s ease, color 0.2s ease',
    backgroundColor: isActive(href) ? '#e0f5f0' : 'transparent',
    whiteSpace: 'nowrap',
    fontWeight: isActive(href) ? 600 : 500,
  });

  const handleLinkHover = (e, href, entering) => {
    e.currentTarget.style.backgroundColor = entering
      ? '#f0faf6'
      : isActive(href) ? '#e0f5f0' : 'transparent';
  };

  useEffect(() => {
    if (!role || !pathname) return;
    const current = ROUTE_ROLES.find(r => pathname.startsWith(r.href));
    if (current && !current.roles.includes(role)) {
      router.push('/');
    }
  }, [role, pathname, router]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <LeafyGreenProvider>
      <header
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          color: '#0f2942',
          boxShadow: '0 4px 10px rgba(0, 0, 0, 0.05)',
          border: '1px solid rgba(220, 240, 230, 0.5)',
          borderRadius: '24px',
          margin: '16px',
          padding: 0,
          position: 'sticky',
          top: '16px',
          zIndex: 100,
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
        }}
      >
        <div
          style={{
            maxWidth: '1600px',
            margin: '0 auto',
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr',
            alignItems: 'center',
            padding: `${spacing[3]}px ${spacing[3]}px`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <img src="/sentinel-logo.png" alt="Sentinel AI Logo" style={{ height: '48px', objectFit: 'contain' }} />
            <img src="/sentinel-name.png" alt="Sentinel AI Name" style={{ height: '48px', objectFit: 'contain' }} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginLeft: '120px' }}>
            <IconButton
              aria-label="Toggle Menu"
              onClick={() => setMenuOpen(!isMenuOpen)}
              className="mobile-menu-toggle"
              style={{ display: 'none' }}
            >
              <Icon glyph={isMenuOpen ? "X" : "Menu"} />
            </IconButton>

            <nav
              style={{
                display: isMenuOpen ? 'block' : 'flex',
                alignItems: 'center',
              }}
            >
              <ul
                style={{
                  display: 'flex',
                  gap: spacing[3],
                  listStyle: 'none',
                  margin: 0,
                  padding: 0,
                  flexDirection: isMenuOpen ? 'column' : 'row',
                }}
              >
                {[
                  { href: '/dashboard', icon: 'Charts', label: 'Dashboard', roles: ['risk_analyst'] },
                  { href: '/investigations', icon: 'ActivityFeed', label: 'Agentic Investigation', roles: ['risk_analyst'] },
                  { href: '/entities', icon: 'Person', label: 'Entity Management', roles: ['risk_analyst'] },
                  { href: '/entity-resolution/enhanced', icon: 'Relationship', label: 'Entity Resolution', roles: ['risk_analyst'] },
                  { href: '/transaction-simulator', icon: 'CreditCard', label: 'Transaction Simulator', roles: ['risk_analyst'] },
                ].filter(link => !link.roles || link.roles.includes(role)).map(link => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      aria-current={isActive(link.href) ? 'page' : undefined}
                      style={navLinkStyle(link.href)}
                      onMouseEnter={(e) => handleLinkHover(e, link.href, true)}
                      onMouseLeave={(e) => handleLinkHover(e, link.href, false)}
                    >
                      <Icon glyph={link.icon} fill={isActive(link.href) ? '#12B8B0' : '#0f2942'} size={16} />
                      <Body style={{ fontFamily: "'Euclid Circular A', sans-serif", color: 'inherit' }}>{link.label}</Body>
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', paddingRight: '24px' }}>
            <div 
              ref={profileRef}
              style={{
                position: 'relative',
              }}
            >
              <button
                onClick={() => setProfileOpen(!isProfileOpen)}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: '4px',
                  cursor: 'pointer',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background-color 0.2s',
                  backgroundColor: isProfileOpen ? 'rgba(0,0,0,0.05)' : 'transparent',
                }}
                title="Profile"
              >
                <img
                  src="/users/67a1000000000000000000002.png"
                  alt="Ana"
                  style={{ width: '32px', height: '32px', objectFit: 'contain', borderRadius: '50%' }}
                />
              </button>

              {isProfileOpen && (
                <div style={{
                  position: 'absolute',
                  top: '100%',
                  right: '0',
                  marginTop: '8px',
                  background: 'white',
                  border: '1px solid #e8edeb',
                  borderRadius: '12px',
                  padding: '16px',
                  minWidth: '200px',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  zIndex: 200,
                }}>
                  <img
                    src="/users/67a1000000000000000000002.png"
                    alt="Ana"
                    style={{ width: '40px', height: '40px', objectFit: 'contain', borderRadius: '50%' }}
                  />
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <Body style={{ fontSize: '15px', fontWeight: 600, lineHeight: '1.2', color: '#0f2942' }}>Ana</Body>
                    <div style={{ fontSize: '13px', color: palette.gray.dark1, marginTop: '2px' }}>Risk Analyst</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main>
        <div style={{ backgroundColor: 'transparent', minHeight: 'calc(100vh - 74px)', padding: spacing[3] }}>
          <div style={{ 
            maxWidth: '1600px', 
            margin: '0 auto', 
            padding: spacing[4],
          }}>
            {children}
          </div>
        </div>
      </main>

      {/* AML Compliance Assistant Chat */}
      <ChatBubble />

      <style jsx global>{`
        /**
         * Euclid
         */

        /* Semibold */
        @font-face {
          font-family: "Euclid Circular A";
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Semibold-WebXL.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Semibold-WebXL.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Semibold.ttf")
              format("truetype");
          font-weight: 700;
          font-style: normal;
        }
        
        /* Semibold Italic */
        @font-face {
          font-family: "Euclid Circular A";
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-SemiboldItalic-WebXL.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-SemiboldItalic-WebXL.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-SemiboldItalic.ttf")
              format("truetype");
          font-weight: 700;
          font-style: italic;
        }
        
        /* Medium */
        @font-face {
          font-family: "Euclid Circular A";
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Medium-WebXL.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Medium-WebXL.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Medium.ttf")
              format("truetype");
          font-weight: 500;
          font-style: normal;
        }
        
        /* Medium Italic */
        @font-face {
          font-family: "Euclid Circular A";
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-MediumItalic-WebXL.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-MediumItalic-WebXL.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-MediumItalic.ttf")
              format("truetype");
          font-weight: 500;
          font-style: italic;
        }
        
        /* Normal */
        @font-face {
          font-family: "Euclid Circular A";
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Regular-WebXL.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Regular-WebXL.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-Regular.ttf")
              format("truetype");
          font-weight: 400, normal;
          font-style: normal;
        }
        
        /* Italic */
        @font-face {
          font-family: "Euclid Circular A";
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-RegularItalic-WebXL.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-RegularItalic-WebXL.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/euclid-circular/EuclidCircularA-RegularItalic.ttf")
              format("truetype");
          font-weight: 400, normal;
          font-style: italic;
        }
        
        /**
          * Value Serif
          */
        
        /* Bold */
        @font-face {
          font-family: "MongoDB Value Serif";
          font-weight: 700, bold;
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Bold.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Bold.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Bold.ttf")
              format("truetype");
        }
        
        /* Medium */
        @font-face {
          font-family: "MongoDB Value Serif";
          font-weight: 500;
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Medium.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Medium.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Medium.ttf")
              format("truetype");
        }
        
        /* Normal */
        @font-face {
          font-family: "MongoDB Value Serif";
          font-weight: 400, normal;
          src: url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Regular.woff")
              format("woff"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Regular.woff2")
              format("woff2"),
            url("https://d2va9gm4j17fy9.cloudfront.net/fonts/value-serif/MongoDBValueSerif-Regular.ttf")
              format("truetype");
        }

        body {
          font-family: "Euclid Circular A", sans-serif;
        }

        @media (max-width: 768px) {
          .mobile-menu-toggle {
            display: block !important;
          }
          
          nav {
            display: ${isMenuOpen ? 'block' : 'none'} !important;
            width: 100%;
            margin-top: ${spacing[3]}px;
          }
          
          nav ul {
            flex-direction: column !important;
          }
        }
        body {
          background-color: #eaf5f0;
          margin: 0;
          padding: 0;
        }
      `}</style>
    </LeafyGreenProvider>
  );
}