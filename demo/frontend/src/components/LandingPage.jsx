import React, { useState, useEffect, useMemo } from 'react'
import { Button, Typography, Space } from 'antd'
import {
    RocketOutlined,
    CodeOutlined,
    EyeOutlined,
    FileTextOutlined,
    SearchOutlined,
    BulbOutlined,
    ExperimentOutlined,
    GlobalOutlined
} from '@ant-design/icons'
import { useLanguage } from '../contexts/LanguageContext'

const { Title, Text } = Typography

function LandingPage({ onEnter }) {
    const [particles, setParticles] = useState([])
    const { language, toggleLanguage, t } = useLanguage()

    useEffect(() => {
        // Generate particle positions - reduced count for better performance
        const newParticles = Array.from({ length: 12 }, (_, i) => ({
            id: i,
            x: Math.random() * 100,
            y: Math.random() * 100,
            size: Math.random() * 3 + 2,
            delay: Math.random() * 3,
            duration: Math.random() * 8 + 8
        }))
        setParticles(newParticles)
    }, [])

    // Use useMemo with language dependency to ensure features update on language change
    const features = useMemo(() => [
        {
            icon: <CodeOutlined />,
            title: t('landing.features.codeAgent.title'),
            subtitle: t('landing.features.codeAgent.subtitle'),
            desc: t('landing.features.codeAgent.desc')
        },
        {
            icon: <EyeOutlined />,
            title: t('landing.features.vision.title'),
            subtitle: t('landing.features.vision.subtitle'),
            desc: t('landing.features.vision.desc')
        },
        {
            icon: <FileTextOutlined />,
            title: t('landing.features.reasoning.title'),
            subtitle: t('landing.features.reasoning.subtitle'),
            desc: t('landing.features.reasoning.desc')
        },
        {
            icon: <SearchOutlined />,
            title: t('landing.features.research.title'),
            subtitle: t('landing.features.research.subtitle'),
            desc: t('landing.features.research.desc')
        }
    ], [language, t])

    return (
        <div style={{
            minHeight: '100vh',
            background: '#b91c1c',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center'
        }}>
            {/* Language Switcher */}
            <div style={{
                position: 'absolute',
                top: '24px',
                right: '24px',
                zIndex: 100
            }}>
                <Button
                    type="text"
                    icon={<GlobalOutlined />}
                    onClick={toggleLanguage}
                    style={{
                        color: 'rgba(255,255,255,0.9)',
                        fontSize: '15px',
                        fontWeight: 500,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 16px',
                        height: 'auto',
                        background: 'rgba(255,255,255,0.15)',
                        border: '1px solid rgba(255,255,255,0.25)',
                        borderRadius: '20px',
                        transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.25)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(255,255,255,0.15)';
                    }}
                >
                    {language === 'zh' ? 'EN' : '中文'}
                </Button>
            </div>

            {/* Simple Background Overlay - optimized for performance */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                opacity: 0.08,
                background: 'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.3) 0%, transparent 60%)'
            }} />

            {/* Animated Particles - simplified for performance */}
            {particles.map(particle => (
                <div
                    key={particle.id}
                    style={{
                        position: 'absolute',
                        left: `${particle.x}%`,
                        top: `${particle.y}%`,
                        width: `${particle.size}px`,
                        height: `${particle.size}px`,
                        background: 'rgba(255,255,255,0.5)',
                        borderRadius: '50%',
                        animation: `floatSimple ${particle.duration}s ease-in-out ${particle.delay}s infinite alternate`
                    }}
                />
            ))}

            {/* Grid Background */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundImage: `
                    linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)
                `,
                backgroundSize: '50px 50px',
                opacity: 0.5
            }} />

            {/* Floating Icons - simplified, static decorative elements */}
            <BulbOutlined style={{
                position: 'absolute',
                fontSize: '40px',
                color: 'rgba(255,255,255,0.12)',
                top: '15%',
                left: '10%'
            }} />
            <ExperimentOutlined style={{
                position: 'absolute',
                fontSize: '50px',
                color: 'rgba(255,255,255,0.1)',
                top: '25%',
                right: '8%'
            }} />
            <CodeOutlined style={{
                position: 'absolute',
                fontSize: '45px',
                color: 'rgba(255,255,255,0.08)',
                bottom: '30%',
                left: '15%'
            }} />
            <SearchOutlined style={{
                position: 'absolute',
                fontSize: '38px',
                color: 'rgba(255,255,255,0.1)',
                bottom: '20%',
                right: '12%'
            }} />

            {/* Static Wave Background - no animation for better performance */}
            <svg
                style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    width: '100%',
                    height: '150px',
                    opacity: 0.1
                }}
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 1440 320"
                preserveAspectRatio="none"
            >
                <path
                    fill="rgba(255,255,255,0.5)"
                    d="M0,96L48,112C96,128,192,160,288,160C384,160,480,128,576,122.7C672,117,768,139,864,138.7C960,139,1056,117,1152,106.7C1248,96,1344,96,1392,96L1440,96L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
                />
            </svg>

            {/* Main Content */}
            <div style={{
                position: 'relative',
                zIndex: 10,
                textAlign: 'center',
                maxWidth: '1200px',
                padding: '0 40px'
            }}>
                {/* Logo Section */}
                <div style={{
                    marginBottom: '40px',
                    animation: 'fadeInDown 0.8s ease-out'
                }}>
                    <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        position: 'relative'
                    }}>
                        <img
                            src="/finsight-logo-v3.png"
                            alt="FinSight Logo"
                            style={{
                                height: '180px',
                                width: '180px',
                                objectFit: 'contain',
                                filter: 'drop-shadow(0 8px 16px rgba(0,0,0,0.25))',
                                position: 'relative',
                                zIndex: 1
                            }}
                            onError={(e) => {
                                e.target.onerror = null;
                                e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="%23fff"/><text x="50" y="65" text-anchor="middle" font-size="50" fill="%23dc2626" font-weight="bold">F</text></svg>';
                            }}
                        />
                    </div>
                </div>

                {/* Title Section */}
                <div style={{ animation: 'fadeInUp 1s ease-out 0.2s both' }}>
                    <Title
                        level={1}
                        style={{
                            color: 'white',
                            fontSize: '64px',
                            fontWeight: 900,
                            margin: '0 0 12px 0',
                            letterSpacing: '3px',
                            textShadow: '0 4px 20px rgba(0,0,0,0.3)',
                            fontFamily: '"Inter", "Segoe UI", sans-serif'
                        }}
                    >
                        {t('landing.title')}
                    </Title>

                    <Text
                        style={{
                            color: 'rgba(255,255,255,0.95)',
                            fontSize: '24px',
                            fontWeight: 500,
                            letterSpacing: '2px',
                            display: 'block',
                            marginBottom: '20px',
                            textShadow: '0 2px 10px rgba(0,0,0,0.2)'
                        }}
                    >
                        {t('landing.subtitle')}
                    </Text>

                    <Text
                        style={{
                            color: 'rgba(255,255,255,0.85)',
                            fontSize: '17px',
                            fontWeight: 400,
                            display: 'block',
                            maxWidth: '750px',
                            margin: '0 auto 44px',
                            lineHeight: '1.8',
                            textShadow: '0 2px 8px rgba(0,0,0,0.2)'
                        }}
                    >
                        {t('landing.description1')}
                        <br />
                        {t('landing.description2')}
                    </Text>
                </div>

                {/* Features Grid - optimized without backdrop-filter */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: '24px',
                    marginBottom: '48px',
                    animation: 'fadeInUp 0.8s ease-out 0.3s both'
                }}>
                    {features.map((feature, index) => (
                        <div
                            key={index}
                            style={{
                                background: 'rgba(255,255,255,0.12)',
                                border: '1px solid rgba(255,255,255,0.18)',
                                borderRadius: '16px',
                                padding: '32px 20px',
                                transition: 'background 0.2s ease',
                                cursor: 'pointer',
                                minHeight: '240px',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                textAlign: 'center'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.background = 'rgba(255,255,255,0.18)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.background = 'rgba(255,255,255,0.12)';
                            }}
                        >
                            <div style={{
                                fontSize: '40px',
                                color: 'white',
                                marginBottom: '14px'
                            }}>
                                {feature.icon}
                            </div>
                            <div style={{
                                fontSize: '15px',
                                fontWeight: 700,
                                color: 'white',
                                marginBottom: '6px',
                                lineHeight: '1.4'
                            }}>
                                {feature.title}
                            </div>
                            <div style={{
                                fontSize: '11px',
                                color: 'rgba(255,255,255,0.6)',
                                marginBottom: '14px',
                                fontStyle: 'italic',
                                letterSpacing: '0.5px'
                            }}>
                                {feature.subtitle}
                            </div>
                            <div style={{
                                fontSize: '12.5px',
                                color: 'rgba(255,255,255,0.75)',
                                lineHeight: '1.6'
                            }}>
                                {feature.desc}
                            </div>
                        </div>
                    ))}
                </div>

                {/* CTA Button */}
                <div style={{ animation: 'fadeInUp 0.8s ease-out 0.5s both' }}>
                    <Button
                        type="primary"
                        size="large"
                        icon={<RocketOutlined />}
                        onClick={onEnter}
                        style={{
                            height: '56px',
                            fontSize: '18px',
                            fontWeight: 600,
                            padding: '0 48px',
                            borderRadius: '28px',
                            background: '#ffffff',
                            border: 'none',
                            color: '#dc2626',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                            transition: 'background 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background = '#f5f5f5';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background = '#ffffff';
                        }}
                    >
                        {t('landing.enterButton')}
                    </Button>

                    <div style={{
                        marginTop: '24px',
                        color: 'rgba(255,255,255,0.7)',
                        fontSize: '14px'
                    }}>
                        {t('landing.slogan')}
                    </div>
                </div>
            </div>

            {/* Simplified Animation Keyframes - optimized for performance */}
            <style>{`
        @keyframes floatSimple {
          0%, 100% {
            transform: translateY(0);
          }
          50% {
            transform: translateY(-10px);
          }
        }

        @keyframes fadeInDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
        </div>
    )
}

export default LandingPage
