// Navigation functionality
class Navigation {
  constructor() {
    this.navToggle = document.getElementById('navToggle');
    this.navMenu = document.getElementById('navMenu');
    this.navLinks = document.querySelectorAll('.nav-link');
    
    this.init();
  }
  
  init() {
    // Mobile menu toggle
    this.navToggle?.addEventListener('click', () => {
      this.navMenu.classList.toggle('active');
      this.updateToggleIcon();
    });
    
    // Close mobile menu when clicking on links
    this.navLinks.forEach(link => {
      link.addEventListener('click', () => {
        this.navMenu.classList.remove('active');
        this.updateToggleIcon();
      });
    });
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.nav-container')) {
        this.navMenu.classList.remove('active');
        this.updateToggleIcon();
      }
    });
    
    // Smooth scroll for anchor links
    this.navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        const href = link.getAttribute('href');
        if (href.startsWith('#')) {
          e.preventDefault();
          const targetId = href.substring(1);
          const targetElement = document.getElementById(targetId);
          
          if (targetElement) {
            const headerHeight = document.querySelector('.header').offsetHeight;
            const targetPosition = targetElement.offsetTop - headerHeight;
            
            window.scrollTo({
              top: targetPosition,
              behavior: 'smooth'
            });
          }
        }
      });
    });
  }
  
  updateToggleIcon() {
    const spans = this.navToggle.querySelectorAll('span');
    if (this.navMenu.classList.contains('active')) {
      spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
      spans[1].style.opacity = '0';
      spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
    } else {
      spans[0].style.transform = 'none';
      spans[1].style.opacity = '1';
      spans[2].style.transform = 'none';
    }
  }
}

// Calculator functionality
class Calculator {
  constructor() {
    this.modal = document.getElementById('calculatorModal');
    this.closeBtn = document.getElementById('closeCalculator');
    this.calculatorBtns = document.querySelectorAll('.calculator-btn');
    this.surfaceInput = document.getElementById('calcSurface');
    this.resultDiv = document.getElementById('calculatorResult');
    this.titleEl = document.getElementById('calculatorTitle');
    
    this.currentProduct = null;
    
    this.init();
  }
  
  init() {
    // Open calculator modal
    this.calculatorBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const price = parseFloat(btn.dataset.price);
        const pcsPerM2 = parseFloat(btn.dataset.pcs);
        const productName = btn.closest('.product-card').querySelector('h4').textContent;
        
        this.currentProduct = { price, pcsPerM2, productName };
        this.titleEl.textContent = `Calculateur - ${productName}`;
        this.surfaceInput.value = '';
        this.resultDiv.innerHTML = '';
        this.resultDiv.classList.remove('show');
        this.modal.classList.add('active');
      });
    });
    
    // Close modal
    this.closeBtn?.addEventListener('click', () => {
      this.modal.classList.remove('active');
    });
    
    // Close modal when clicking outside
    this.modal?.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.modal.classList.remove('active');
      }
    });
    
    // Calculate on input change
    this.surfaceInput?.addEventListener('input', () => {
      this.calculate();
    });
  }
  
  calculate() {
    const surface = parseFloat(this.surfaceInput.value);
    
    if (!surface || surface <= 0 || !this.currentProduct) {
      this.resultDiv.classList.remove('show');
      return;
    }
    
    const { price, pcsPerM2, productName } = this.currentProduct;
    const totalPieces = Math.ceil(surface * pcsPerM2);
    const totalPrice = totalPieces * price;
    
    this.resultDiv.innerHTML = `
      <h4>Résultat du calcul</h4>
      <div class="result-item">
        <span>Surface:</span>
        <span>${surface} m²</span>
      </div>
      <div class="result-item">
        <span>Pièces nécessaires:</span>
        <span>${totalPieces} pcs</span>
      </div>
      <div class="result-item">
        <span>Prix unitaire:</span>
        <span>${price.toLocaleString()} Ar</span>
      </div>
      <div class="result-item total">
        <span>Prix total estimé:</span>
        <span>${totalPrice.toLocaleString()} Ar</span>
      </div>
      <p style="margin-top: 1rem; font-size: 0.9rem; color: var(--color-gray-dark); font-style: italic;">
        Prix indicatif - Contactez-nous pour un devis personnalisé
      </p>
    `;
    
    this.resultDiv.classList.add('show');
  }
}

// Gallery lightbox functionality
class Lightbox {
  constructor() {
    this.lightbox = document.getElementById('lightbox');
    this.lightboxImage = document.getElementById('lightboxImage');
    this.closeBtn = document.getElementById('closeLightbox');
    this.galleryItems = document.querySelectorAll('.gallery-item');
    
    this.init();
  }
  
  init() {
    // Open lightbox
    this.galleryItems.forEach(item => {
      item.addEventListener('click', () => {
        const imageUrl = item.dataset.image;
        const altText = item.querySelector('img').alt;
        
        this.lightboxImage.src = imageUrl;
        this.lightboxImage.alt = altText;
        this.lightbox.classList.add('active');
      });
    });
    
    // Close lightbox
    this.closeBtn?.addEventListener('click', () => {
      this.lightbox.classList.remove('active');
    });
    
    // Close lightbox when clicking outside
    this.lightbox?.addEventListener('click', (e) => {
      if (e.target === this.lightbox) {
        this.lightbox.classList.remove('active');
      }
    });
    
    // Close lightbox with Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.lightbox.classList.contains('active')) {
        this.lightbox.classList.remove('active');
      }
    });
  }
}

// Contact form functionality
class ContactForm {
  constructor() {
    this.form = document.getElementById('contactForm');
    this.init();
  }
  
  init() {
    this.form?.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSubmit();
    });
  }
  
  async handleSubmit() {
    const formData = new FormData(this.form);
    const data = Object.fromEntries(formData.entries());
    
    // Basic validation
    if (!data.name || !data.phone || !data.location) {
      this.showMessage('Veuillez remplir tous les champs obligatoires.', 'error');
      return;
    }
    
    // Show loading state
    const submitBtn = this.form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.innerHTML = '<span class="loading"></span> Envoi en cours...';
    submitBtn.disabled = true;
    
    try {
      // Simulate form submission (replace with actual endpoint)
      await this.simulateSubmission(data);
      
      // Show success message
      this.showMessage('Votre demande a été envoyée avec succès ! Nous vous contacterons rapidement.', 'success');
      this.form.reset();
      
    } catch (error) {
      console.error('Form submission error:', error);
      this.showMessage('Une erreur est survenue. Veuillez réessayer ou nous contacter directement.', 'error');
    } finally {
      // Reset button state
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    }
  }
  
  async simulateSubmission(data) {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Log form data (in real implementation, send to server)
    console.log('Form submission:', data);
    
    // Create mailto link as fallback
    const subject = encodeURIComponent('Demande de devis - HOURDIS MADAGASCAR');
    const body = encodeURIComponent(`
Nom: ${data.name}
Téléphone: ${data.phone}
Email: ${data.email || 'Non renseigné'}
Localisation: ${data.location}
Surface: ${data.surface || 'Non renseignée'} m²
Message: ${data.message || 'Aucun message'}
    `);
    
    const mailtoLink = `mailto:contact@hourdismg.com?subject=${subject}&body=${body}`;
    
    // In a real implementation, you would send this data to your server
    // For now, we'll just log it and optionally open the mailto link
    console.log('Mailto link:', mailtoLink);
  }
  
  showMessage(message, type) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.form-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `form-message ${type}`;
    messageEl.style.cssText = `
      padding: 1rem;
      margin: 1rem 0;
      border-radius: var(--border-radius);
      font-weight: 500;
      ${type === 'success' ? 
        'background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb;' :
        'background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;'
      }
    `;
    messageEl.textContent = message;
    
    // Insert message after form
    this.form.insertAdjacentElement('afterend', messageEl);
    
    // Auto-remove success messages after 5 seconds
    if (type === 'success') {
      setTimeout(() => {
        messageEl.remove();
      }, 5000);
    }
  }
}

// Scroll animations
class ScrollAnimations {
  constructor() {
    this.init();
  }
  
  init() {
    // Intersection Observer for fade-in animations
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in-up');
        }
      });
    }, observerOptions);
    
    // Observe elements for animation
    const animateElements = document.querySelectorAll(`
      .advantage-item,
      .product-card,
      .choice-card,
      .benefit-item,
      .gallery-item,
      .type-card
    `);
    
    animateElements.forEach(el => {
      observer.observe(el);
    });
  }
}

// Header scroll effect
class HeaderScroll {
  constructor() {
    this.header = document.querySelector('.header');
    this.init();
  }
  
  init() {
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      
      // Add background opacity based on scroll
      const opacity = Math.min(scrollTop / 100, 1);
      this.header.style.backgroundColor = `rgba(255, 255, 255, ${0.95 + (0.05 * opacity)})`;
      
      // Hide/show header on scroll (optional)
      if (scrollTop > lastScrollTop && scrollTop > 100) {
        // Scrolling down
        this.header.style.transform = 'translateY(-100%)';
      } else {
        // Scrolling up
        this.header.style.transform = 'translateY(0)';
      }
      
      lastScrollTop = scrollTop;
    });
  }
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new Navigation();
  new Calculator();
  new Lightbox();
  new ContactForm();
  new ScrollAnimations();
  new HeaderScroll();
  
  // Add smooth reveal animation to hero content
  const heroContent = document.querySelector('.hero-content');
  if (heroContent) {
    setTimeout(() => {
      heroContent.classList.add('fade-in-up');
    }, 500);
  }
});

// Service Worker registration for PWA capabilities (optional)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => {
        console.log('SW registered: ', registration);
      })
      .catch(registrationError => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// Performance optimization: Lazy loading for images
document.addEventListener('DOMContentLoaded', () => {
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          if (img.dataset.src) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
          }
          img.classList.remove('lazy');
          observer.unobserve(img);
        }
      });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });
  }
});

// Utility functions
const utils = {
  // Format currency for Madagascar Ariary
  formatCurrency: (amount) => {
    return new Intl.NumberFormat('fr-MG', {
      style: 'currency',
      currency: 'MGA',
      minimumFractionDigits: 0
    }).format(amount);
  },
  
  // Debounce function for performance
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },
  
  // Throttle function for scroll events
  throttle: (func, limit) => {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    }
  }
};

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    Navigation,
    Calculator,
    Lightbox,
    ContactForm,
    ScrollAnimations,
    HeaderScroll,
    utils
  };
}