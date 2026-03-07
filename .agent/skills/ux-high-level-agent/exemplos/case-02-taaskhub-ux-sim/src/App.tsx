import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import {
  ChevronDown,
  LayoutTemplate,
  Menu,
  MessageCircle,
  Play,
  Sparkles,
  X,
} from 'lucide-react'
import { type ReactNode, useState } from 'react'
import './App.css'

type StatCard = {
  value: string
  label: string
  body: string
  preview: 'dashboard' | 'thumbnails' | 'figma'
}

type DemoCard = {
  title: string
  category: string
  variant: 'homepage' | 'company' | 'pricing' | 'case' | 'integration' | 'contact'
}

type InnerPageCard = {
  title: string
  subtitle: string
  accent: 'violet' | 'yellow' | 'green' | 'pink' | 'ink'
  content: 'about' | 'pricing' | 'case-study' | 'integration'
}

const navItems = ['All Pages', 'Features', 'Contacts']

const stats: StatCard[] = [
  {
    value: '19',
    label: 'Unique Pages',
    body: 'Ready to use pages to launch your website fast.',
    preview: 'dashboard',
  },
  {
    value: '62+',
    label: 'Sections & Blocks',
    body: 'Build unique pages with simple drag and drop.',
    preview: 'thumbnails',
  },
  {
    value: 'Figma',
    label: 'File Included',
    body: 'Email your receipt and receive the editable Figma source file.',
    preview: 'figma',
  },
]

const homepages: DemoCard[] = [
  { title: 'Homepage 1', category: 'Light SaaS Hero', variant: 'homepage' },
  { title: 'Homepage 2', category: 'Startup Dashboard', variant: 'homepage' },
  { title: 'Homepage 3', category: 'Productivity Suite', variant: 'homepage' },
]

const innerPages: InnerPageCard[] = [
  { title: 'About Us', subtitle: 'Company', accent: 'ink', content: 'about' },
  { title: 'Pricing', subtitle: 'Plans', accent: 'violet', content: 'pricing' },
  { title: 'Case Study', subtitle: 'Stories', accent: 'yellow', content: 'case-study' },
  { title: 'Integration', subtitle: 'Tooling', accent: 'green', content: 'integration' },
  { title: 'Contact Us', subtitle: 'Book a Demo', accent: 'pink', content: 'case-study' },
  { title: 'Case Study Details', subtitle: 'Long-form', accent: 'ink', content: 'case-study' },
]

const sectionReveal = {
  hidden: { opacity: 0, y: 26 },
  show: { opacity: 1, y: 0 },
}

function Reveal({ children, className, delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const reduceMotion = useReducedMotion()
  if (reduceMotion) return <div className={className}>{children}</div>

  return (
    <motion.div
      className={className}
      variants={sectionReveal}
      initial="hidden"
      whileInView="show"
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.5, ease: 'easeOut', delay }}
    >
      {children}
    </motion.div>
  )
}

function Brand() {
  return (
    <div className="brand" aria-label="TaskHub">
      <span className="brand-mark" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
      </span>
      <span>TaskHub</span>
    </div>
  )
}

function BubbleTag({ side, text }: { side: 'left' | 'right'; text: string }) {
  return (
    <div className={`bubble-tag ${side}`}>
      <span className="bubble-arrow" />
      <span className="bubble-chip">{text}</span>
    </div>
  )
}

function TinyBrowserChrome() {
  return (
    <div className="mini-browser-bar">
      <Brand />
      <div className="mini-nav">Home Features Pricing Blog Contacts</div>
      <button className="mini-cta">Start Your Free Trial</button>
    </div>
  )
}

function DashboardPreview() {
  return (
    <div className="preview-card preview-dashboard">
      <TinyBrowserChrome />
      <div className="dashboard-preview-grid">
        <div className="dashboard-left-col">
          <h4>Easy task management for your startups</h4>
          <div className="dashboard-pill-row">
            <span className="pill violet">Startups</span>
            <span className="pill yellow">Teams</span>
            <span className="pill light">Scale Fast</span>
          </div>
          <div className="graph-card">
            <div className="graph-bars">
              {Array.from({ length: 12 }).map((_, i) => (
                <span key={i} style={{ height: `${20 + ((i * 17) % 55)}px` }} />
              ))}
            </div>
            <div className="graph-caption">Weekly productivity growth</div>
          </div>
        </div>
        <div className="dashboard-side-col">
          <div className="mini-widget">
            <div className="mini-title">Tasks done</div>
            <strong>92%</strong>
          </div>
          <div className="mini-widget">
            <div className="mini-title">Members</div>
            <strong>23</strong>
          </div>
          <div className="mini-widget stacked">
            <div className="mini-title">Status</div>
            <div className="status-list">
              <span className="dot green" /> Active
              <span className="dot violet" /> Planning
              <span className="dot yellow" /> Review
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ThumbnailsPreview() {
  return (
    <div className="preview-card preview-thumbs">
      <div className="thumb-grid">
        {Array.from({ length: 4 }).map((_, idx) => (
          <div className="thumb-large" key={`lg-${idx}`}>
            <TinyBrowserChrome />
            <div className="thumb-content">
              <div className="thumb-title" />
              <div className="thumb-subtitle" />
              <div className="thumb-row">
                <div className="thumb-box violet" />
                <div className="thumb-box yellow" />
                <div className="thumb-box light" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function FigmaPreview() {
  return (
    <div className="preview-card preview-figma">
      <div className="figma-icon" aria-hidden="true">
        <span className="r1" />
        <span className="r2" />
        <span className="r3" />
        <span className="r4" />
        <span className="r5" />
      </div>
      <div className="figma-stage">
        <div className="figma-left">
          <div className="figma-list-header" />
          {Array.from({ length: 7 }).map((_, i) => (
            <div className="figma-list-item" key={i} />
          ))}
        </div>
        <div className="figma-board">
          {Array.from({ length: 8 }).map((_, i) => (
            <div className="figma-frame" key={i}>
              <div className="figma-frame-top" />
              <div className="figma-frame-body" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function FeatureShowcaseCard({ item, index }: { item: StatCard; index: number }) {
  return (
    <Reveal className={`feature-showcase-card card-${item.preview}`} delay={index * 0.05}>
      <div className="feature-card-shell">
        <div className="feature-card-left">
          <div className="feature-card-value">{item.value}</div>
          <h3>{item.label}</h3>
          <p>{item.body}</p>
        </div>
        <div className="feature-card-right">
          {item.preview === 'dashboard' ? <DashboardPreview /> : null}
          {item.preview === 'thumbnails' ? <ThumbnailsPreview /> : null}
          {item.preview === 'figma' ? <FigmaPreview /> : null}
        </div>
      </div>
    </Reveal>
  )
}

function HomepageTile({ card }: { card: DemoCard }) {
  return (
    <div className="demo-tile">
      <div className="demo-screen">
        <TinyBrowserChrome />
        <div className="demo-hero">
          <div className="demo-badge" />
          <div className="demo-heading" />
          <div className="demo-subheading" />
          <div className="demo-btn-row">
            <span className="btn-fake yellow" />
            <span className="btn-fake white" />
          </div>
        </div>
        <div className="demo-panels">
          <div className="panel-fake violet" />
          <div className="panel-fake yellow" />
          <div className="panel-fake white" />
        </div>
      </div>
      <div className="tile-meta">
        <strong>{card.title}</strong>
        <span>{card.category}</span>
      </div>
    </div>
  )
}

function InnerPagePreview({ card }: { card: InnerPageCard }) {
  return (
    <div className="inner-page-tile">
      <div className="inner-page-screen">
        <TinyBrowserChrome />
        <div className={`inner-page-content accent-${card.accent}`}>
          {card.content === 'about' ? <AboutMock /> : null}
          {card.content === 'pricing' ? <PricingMock /> : null}
          {card.content === 'case-study' ? <CaseStudyMock /> : null}
          {card.content === 'integration' ? <IntegrationMock /> : null}
        </div>
      </div>
      <div className="tile-meta">
        <strong>{card.title}</strong>
        <span>{card.subtitle}</span>
      </div>
    </div>
  )
}

function AboutMock() {
  return (
    <div className="mock-stack about-mock">
      <div className="mock-title" />
      <div className="mock-subtitle" />
      <div className="mock-row split">
        <div className="mock-photo" />
        <div className="mock-dark-card" />
      </div>
      <div className="mock-logos" />
      <div className="mock-title sm" />
    </div>
  )
}

function PricingMock() {
  return (
    <div className="mock-stack pricing-mock">
      <div className="mock-title" />
      <div className="mock-subtitle" />
      <div className="pricing-mock-grid">
        <div className="pricing-card-mock" />
        <div className="pricing-card-mock highlight" />
        <div className="pricing-card-mock" />
      </div>
    </div>
  )
}

function CaseStudyMock() {
  return (
    <div className="mock-stack case-mock">
      <div className="mock-title" />
      <div className="mock-subtitle" />
      <div className="mock-row split">
        <div className="mock-copy-panel" />
        <div className="mock-photo" />
      </div>
      <div className="mock-row split compact">
        <div className="mock-copy-panel" />
        <div className="mock-photo small" />
      </div>
    </div>
  )
}

function IntegrationMock() {
  return (
    <div className="mock-stack integration-mock">
      <div className="mock-title" />
      <div className="mock-subtitle" />
      <div className="integration-grid">
        {Array.from({ length: 4 }).map((_, i) => (
          <div className="integration-box" key={i}>
            <span className={`integration-dot ${['pink', 'green', 'ink', 'violet'][i]}`} />
            <div className="integration-lines" />
          </div>
        ))}
      </div>
      <div className="mock-content-wide" />
    </div>
  )
}

function FooterCTA() {
  return (
    <section className="final-cta">
      <div className="final-cta-content">
        <span className="eyebrow yellow">Get Started</span>
        <h2>Build a trendy website within days, not weeks!</h2>
        <p>
          TaskHub-inspired multi-page SaaS template simulation with reusable sections, playful visual accents and scalable component patterns.
        </p>
        <button className="btn btn-dark"><Play size={14} fill="currentColor" /> Get This Template</button>
      </div>
      <div className="final-cta-device">
        <div className="phone-stack">
          <div className="phone-card front">
            <div className="phone-screen">
              <div className="phone-chip yellow" />
              <div className="phone-title" />
              <div className="phone-lines" />
              <div className="phone-panels">
                <div />
                <div />
                <div />
              </div>
            </div>
          </div>
          <div className="phone-card back" />
        </div>
      </div>
    </section>
  )
}

function FramerLikeWidget() {
  return (
    <div className="floating-promo" aria-hidden="true">
      <button className="promo-pill white">Get This Template</button>
      <button className="promo-pill blue">Unlock 200+ Templates</button>
      <button className="promo-pill dark">Access 4200+ Components</button>
      <button className="promo-badge">Made in Framer</button>
    </div>
  )
}

function App() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="taskhub-app">
      <header className="site-header">
        <div className="nav-shell">
          <Brand />
          <nav className="nav-links" aria-label="Primary">
            {navItems.map((item) => (
              <a key={item} href={`#${item.toLowerCase().replace(/\s+/g, '-')}`}>
                {item}
                {item === 'All Pages' ? <ChevronDown size={14} /> : null}
              </a>
            ))}
          </nav>
          <button className="btn btn-dark desktop-cta">Get This Template</button>
          <button className="menu-btn" onClick={() => setMenuOpen((v) => !v)} aria-label="Toggle menu">
            {menuOpen ? <X size={20} /> : <Menu size={22} />}
          </button>
        </div>
        <AnimatePresence>
          {menuOpen ? (
            <motion.div
              className="mobile-menu"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              {navItems.map((item) => (
                <a key={item} href={`#${item.toLowerCase().replace(/\s+/g, '-')}`} onClick={() => setMenuOpen(false)}>
                  {item}
                </a>
              ))}
              <button className="btn btn-dark">Get This Template</button>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </header>

      <main>
        <section className="hero-section">
          <div className="hero-panel">
            <Reveal className="hero-copy">
              <h1>Launch your SaaS or startup website with Taskhub in days, not weeks.</h1>
              <p>Get a ready to launch Framer-style template for building any kind of modern SaaS website.</p>
              <div className="hero-actions">
                <button className="btn btn-yellow">Get This Template</button>
                <button className="btn btn-outline">Explore All Demos</button>
              </div>
              <BubbleTag side="left" text="Charles" />
              <BubbleTag side="right" text="You" />
            </Reveal>
          </div>
        </section>

        <section className="feature-showcase" id="features">
          {stats.map((item, index) => (
            <FeatureShowcaseCard key={item.label} item={item} index={index} />
          ))}
        </section>

        <section className="section-block" id="all-pages">
          <Reveal className="section-header">
            <span className="eyebrow violet">03 Homepages</span>
            <h2>View Page</h2>
            <p>Three playful landing variants with shared tokens, reusable sections and differentiated hero structures.</p>
          </Reveal>
          <div className="tiles-grid homepages-grid">
            {homepages.map((card, index) => (
              <Reveal key={card.title} delay={index * 0.05}>
                <HomepageTile card={card} />
              </Reveal>
            ))}
          </div>
        </section>

        <section className="section-block">
          <Reveal className="section-header">
            <span className="eyebrow mint">16 Inner Pages</span>
            <h2>Browse Inner Pages</h2>
            <p>Marketing, pricing, case studies and integrations pages built with the same visual language and modular cards.</p>
          </Reveal>
          <div className="tiles-grid inner-pages-grid">
            {innerPages.map((card, index) => (
              <Reveal key={`${card.title}-${index}`} delay={(index % 3) * 0.04}>
                <InnerPagePreview card={card} />
              </Reveal>
            ))}
          </div>
        </section>

        <section className="section-block two-up-grid" id="contacts">
          <Reveal className="big-panel card-panel" delay={0.03}>
            <div className="big-panel-header">
              <span className="eyebrow violet">Case Study</span>
              <h3>Success stories from our clients</h3>
              <p>Showcase long-form content and proof metrics with a clear split between story and supporting imagery.</p>
            </div>
            <div className="story-layout">
              <div className="story-copy">
                <h4>Improving project visibility for a remote agency</h4>
                <p>
                  Taskhub-inspired case study pattern with a high-signal headline, compact metrics, and primary CTA in a quiet layout.
                </p>
                <div className="mini-metrics">
                  <div><strong>50%</strong><span>Faster planning</span></div>
                  <div><strong>2x</strong><span>Clearer reporting</span></div>
                  <div><strong>70%</strong><span>Client satisfaction</span></div>
                </div>
                <button className="btn btn-dark sm">Read full story</button>
              </div>
              <div className="story-photo" />
            </div>
          </Reveal>

          <Reveal className="big-panel card-panel" delay={0.08}>
            <div className="big-panel-header">
              <span className="eyebrow yellow">Case Study Details</span>
              <h3>Improving project visibility for a remote agency</h3>
              <p>Long-form article layout pattern with media lead and readable paragraph rhythm for conversion-support content.</p>
            </div>
            <div className="article-photo" />
            <div className="article-lines">
              <div className="line w-100" />
              <div className="line w-92" />
              <div className="line w-96" />
            </div>
          </Reveal>
        </section>

        <section className="section-block two-up-grid">
          <Reveal className="big-panel card-panel" delay={0.02}>
            <div className="big-panel-header">
              <span className="eyebrow mint">Integrations</span>
              <h3>Connect with your favorite tools</h3>
              <p>Visual grid of integration cards with soft icons and low-friction scanning for supported platforms.</p>
            </div>
            <div className="integration-card-grid">
              {['CollabDesk', 'Syncly', 'Flowbase', 'Cronify'].map((name, i) => (
                <div className="integration-tile" key={name}>
                  <span className={`integration-logo l${i + 1}`} />
                  <strong>{name}</strong>
                  <p>Streamline team collaboration with shared docs and automations.</p>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal className="big-panel card-panel" delay={0.07}>
            <div className="big-panel-header">
              <span className="eyebrow violet">Integration Details</span>
              <h3>Integration with Chatrack</h3>
              <p>Detailed partner page layout with summary, highlights, and content blocks for integration-specific flows.</p>
            </div>
            <div className="detail-layout">
              <div className="detail-hero-card">
                <div className="detail-badge" />
                <div className="detail-title" />
                <div className="detail-icons">
                  <span /> <span /> <span /> <span />
                </div>
              </div>
              <div className="detail-text-card">
                <div className="line w-100" />
                <div className="line w-90" />
                <div className="line w-95" />
                <div className="line w-70" />
              </div>
            </div>
          </Reveal>
        </section>

        <Reveal className="section-block final-cta-wrap">
          <FooterCTA />
        </Reveal>
      </main>

      <footer className="site-footer">
        <div className="footer-top">
          <Brand />
          <div className="footer-links">
            <div>
              <h4>Pages</h4>
              <a href="#">Homepage 1</a>
              <a href="#">Homepage 2</a>
              <a href="#">Pricing</a>
              <a href="#">Case Study</a>
            </div>
            <div>
              <h4>Utility</h4>
              <a href="#">Changelog</a>
              <a href="#">Privacy</a>
              <a href="#">Terms</a>
              <a href="#">404</a>
            </div>
            <div>
              <h4>Contact</h4>
              <a href="mailto:hello@framerbite.com">hello@framerbite.com</a>
              <a href="#">Book A Demo</a>
              <a href="#">Features</a>
              <a href="#">Blog</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <span>TaskHub-inspired simulation (original code)</span>
          <div className="footer-badges">
            <span><LayoutTemplate size={14} /> 19 pages</span>
            <span><Sparkles size={14} /> 62+ sections</span>
            <span><MessageCircle size={14} /> Modern SaaS UI kit</span>
          </div>
        </div>
      </footer>

      <FramerLikeWidget />
    </div>
  )
}

export default App
