# CLAUDE.md - AI Assistant Guide for FinanzApp

## Project Overview

**FinanzApp** is a financial management application designed to help users track their finances, manage budgets, and analyze spending patterns.

### Project Status
- **Stage**: Initial Development
- **Repository**: Nojands/FinanzApp
- **Primary Language**: TBD (Recommended: TypeScript/JavaScript for web, or Python for data-heavy operations)

## Repository Structure

The following structure should be maintained as the project develops:

```
FinanzApp/
├── .github/                    # GitHub workflows and templates
│   ├── workflows/             # CI/CD pipelines
│   └── ISSUE_TEMPLATE/        # Issue templates
├── docs/                      # Project documentation
│   ├── architecture.md        # System architecture
│   ├── api/                   # API documentation
│   └── user-guide/            # User documentation
├── src/                       # Source code
│   ├── components/            # UI components (if web-based)
│   ├── services/              # Business logic services
│   ├── models/                # Data models
│   ├── utils/                 # Utility functions
│   ├── api/                   # API routes/endpoints
│   └── config/                # Configuration files
├── tests/                     # Test files
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
├── scripts/                   # Build and deployment scripts
├── migrations/                # Database migrations
├── public/                    # Static assets (if web-based)
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── package.json               # Dependencies (if Node.js)
├── requirements.txt           # Dependencies (if Python)
├── README.md                  # Project README
├── CONTRIBUTING.md            # Contribution guidelines
├── LICENSE                    # Project license
└── CLAUDE.md                  # This file
```

## Technology Stack Recommendations

### Backend Options
- **Node.js + Express/Fastify**: For REST APIs
- **Python + FastAPI/Django**: For data-heavy operations
- **Go**: For high-performance requirements

### Frontend Options
- **React + TypeScript**: Modern, type-safe UI
- **Vue.js**: Progressive framework
- **Next.js**: Full-stack React framework with SSR

### Database
- **PostgreSQL**: Recommended for financial data (ACID compliance)
- **MongoDB**: For flexible schema requirements
- **SQLite**: For prototyping/development

### Additional Tools
- **Prisma/TypeORM**: Database ORM
- **Jest/Vitest**: Testing framework
- **Docker**: Containerization
- **Redis**: Caching layer

## Development Workflow

### Branch Strategy

1. **Main Branch**: Production-ready code
2. **Develop Branch**: Integration branch for features
3. **Feature Branches**: `feature/description` or `claude/session-id`
4. **Hotfix Branches**: `hotfix/description`

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/add-transaction-tracking

# Make changes and commit
git add .
git commit -m "feat: add transaction tracking functionality"

# Push to remote
git push -u origin feature/add-transaction-tracking

# Create pull request for review
```

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

**Examples:**
```
feat: add user authentication module
fix: resolve transaction calculation rounding error
docs: update API documentation for transactions endpoint
refactor: simplify budget calculation logic
test: add unit tests for transaction service
```

## Coding Conventions

### General Principles

1. **DRY (Don't Repeat Yourself)**: Avoid code duplication
2. **SOLID Principles**: Follow object-oriented design principles
3. **KISS (Keep It Simple, Stupid)**: Prefer simple solutions
4. **YAGNI (You Aren't Gonna Need It)**: Don't add unnecessary features

### Code Style

#### TypeScript/JavaScript
- Use **ESLint** and **Prettier** for code formatting
- Prefer `const` over `let`, avoid `var`
- Use async/await over callbacks
- Use TypeScript for type safety
- Prefer functional programming patterns
- Use meaningful variable and function names

```typescript
// Good
const calculateMonthlyBudget = async (userId: string): Promise<Budget> => {
  const transactions = await getTransactionsByUser(userId);
  return computeBudget(transactions);
};

// Avoid
var calcBudget = function(id) {
  // callback hell
};
```

#### Python
- Follow **PEP 8** style guide
- Use type hints
- Use virtual environments
- Prefer list comprehensions when appropriate

```python
# Good
def calculate_monthly_budget(user_id: str) -> Budget:
    """Calculate monthly budget for a user."""
    transactions = get_user_transactions(user_id)
    return compute_budget(transactions)

# Avoid
def calc(id):
    pass
```

### Naming Conventions

- **Files**: kebab-case for files (`transaction-service.ts`)
- **Classes**: PascalCase (`TransactionService`)
- **Functions/Methods**: camelCase (`calculateTotal`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_TRANSACTION_AMOUNT`)
- **Variables**: camelCase (`userBalance`)
- **Database Tables**: snake_case (`user_transactions`)

### Error Handling

Always implement proper error handling:

```typescript
try {
  const result = await riskyOperation();
  return result;
} catch (error) {
  logger.error('Operation failed', { error, context });
  throw new AppError('User-friendly error message', 500);
}
```

## Security Considerations

⚠️ **CRITICAL**: This is a financial application. Security is paramount.

### Security Best Practices

1. **Never commit secrets**: Use environment variables
2. **Input validation**: Validate all user inputs
3. **SQL Injection**: Use parameterized queries or ORM
4. **XSS Protection**: Sanitize outputs
5. **CSRF Protection**: Implement CSRF tokens
6. **Authentication**: Use secure auth methods (JWT, OAuth2)
7. **HTTPS Only**: Always use HTTPS in production
8. **Rate Limiting**: Implement rate limiting on APIs
9. **Audit Logging**: Log all financial transactions
10. **Data Encryption**: Encrypt sensitive data at rest

### Environment Variables

Never commit `.env` files. Always provide `.env.example`:

```env
# .env.example
DATABASE_URL=postgresql://user:password@localhost:5432/finanzapp
JWT_SECRET=your-secret-key-here
API_KEY=your-api-key
NODE_ENV=development
PORT=3000
```

### Sensitive Data Handling

```typescript
// Good: Hash passwords
const hashedPassword = await bcrypt.hash(password, 10);

// Good: Sanitize financial data in logs
logger.info('Transaction created', {
  userId,
  amount: '***', // Don't log actual amounts
  type
});

// Bad: Never log sensitive data
logger.info('User data', { password, ssn, cardNumber });
```

## Testing Requirements

### Test Coverage Goals
- **Minimum**: 80% code coverage
- **Critical paths**: 100% coverage for financial calculations
- **Integration tests**: Cover all API endpoints

### Test Structure

```typescript
// Unit test example
describe('TransactionService', () => {
  describe('calculateBalance', () => {
    it('should calculate correct balance with multiple transactions', () => {
      const transactions = [
        { amount: 100, type: 'income' },
        { amount: 50, type: 'expense' }
      ];
      const balance = calculateBalance(transactions);
      expect(balance).toBe(50);
    });

    it('should handle empty transaction list', () => {
      const balance = calculateBalance([]);
      expect(balance).toBe(0);
    });
  });
});
```

### Test Naming Convention
- Describe what the test does in plain English
- Use `should` or `it` pattern
- Group related tests with `describe`

## Database Conventions

### Schema Design
- Use proper foreign keys and constraints
- Index frequently queried columns
- Use transactions for multi-step operations
- Implement soft deletes for financial records

### Migration Strategy
- Never edit existing migrations
- Always create new migrations for changes
- Test migrations on staging before production
- Include both `up` and `down` migrations

```sql
-- Example migration
-- migrations/001_create_transactions.sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  amount DECIMAL(10, 2) NOT NULL,
  currency VARCHAR(3) NOT NULL DEFAULT 'USD',
  type VARCHAR(20) NOT NULL,
  category VARCHAR(50),
  description TEXT,
  transaction_date TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
```

## API Design Conventions

### RESTful API Guidelines

- Use proper HTTP methods: GET, POST, PUT, PATCH, DELETE
- Use plural nouns for resources: `/api/transactions`, `/api/users`
- Use nested routes for relationships: `/api/users/:id/transactions`
- Version your API: `/api/v1/transactions`
- Return appropriate status codes

### API Response Format

```typescript
// Success response
{
  "success": true,
  "data": {
    "id": "123",
    "amount": 100.50,
    "currency": "USD"
  },
  "meta": {
    "timestamp": "2025-11-15T10:30:00Z"
  }
}

// Error response
{
  "success": false,
  "error": {
    "code": "INVALID_AMOUNT",
    "message": "Transaction amount must be positive",
    "details": {}
  },
  "meta": {
    "timestamp": "2025-11-15T10:30:00Z"
  }
}

// Paginated response
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "total": 100,
    "totalPages": 5
  }
}
```

### Status Codes
- `200 OK`: Successful GET, PUT, PATCH
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Documentation Standards

### Code Documentation

Use JSDoc/TSDoc for functions and classes:

```typescript
/**
 * Calculates the monthly budget based on user transactions
 * @param userId - The unique identifier of the user
 * @param month - The month to calculate (1-12)
 * @param year - The year to calculate
 * @returns Promise resolving to the calculated budget
 * @throws {UserNotFoundError} If user doesn't exist
 * @example
 * const budget = await calculateMonthlyBudget('user-123', 11, 2025);
 */
async function calculateMonthlyBudget(
  userId: string,
  month: number,
  year: number
): Promise<Budget> {
  // Implementation
}
```

### README Requirements

Every major module/service should have a README explaining:
- Purpose and functionality
- Setup instructions
- Usage examples
- API reference (if applicable)
- Configuration options

## AI Assistant Guidelines

### When Working on This Project

1. **Always read relevant files first** before making changes
2. **Use TypeScript** for type safety when applicable
3. **Follow security best practices** - this is a financial app
4. **Write tests** for new functionality
5. **Update documentation** when adding features
6. **Use meaningful commit messages** following conventions
7. **Never commit sensitive data** (keys, passwords, tokens)
8. **Ask for clarification** when requirements are ambiguous

### Task Workflow for AI Assistants

1. **Understand the requirement**
   - Read the issue/request carefully
   - Ask clarifying questions if needed

2. **Research the codebase**
   - Use Explore agent for understanding existing patterns
   - Read related files and tests
   - Understand dependencies

3. **Plan the implementation**
   - Create a todo list with TodoWrite tool
   - Break down complex tasks into steps
   - Consider edge cases and error scenarios

4. **Implement the solution**
   - Write clean, documented code
   - Follow established patterns
   - Handle errors properly
   - Add logging where appropriate

5. **Test the changes**
   - Write unit tests
   - Write integration tests if needed
   - Manually test critical paths
   - Ensure existing tests still pass

6. **Document the changes**
   - Update code comments
   - Update README if needed
   - Document API changes
   - Update CHANGELOG

7. **Commit and push**
   - Use conventional commit messages
   - Push to feature branch
   - Create PR with detailed description

### Common Pitfalls to Avoid

❌ **Don't**:
- Commit without testing
- Ignore existing code patterns
- Skip error handling
- Log sensitive financial data
- Use hardcoded values instead of config
- Make breaking changes without documentation
- Commit directly to main/master
- Use `any` type in TypeScript
- Skip input validation
- Ignore security considerations

✅ **Do**:
- Follow established patterns
- Write self-documenting code
- Add tests for new features
- Use type-safe code
- Validate all inputs
- Handle errors gracefully
- Log appropriately (without sensitive data)
- Update documentation
- Ask for clarification when uncertain
- Consider performance implications

### Financial Calculations

⚠️ **CRITICAL**: Always use proper decimal handling for financial calculations

```typescript
// Good: Use decimal libraries
import Decimal from 'decimal.js';

const total = new Decimal(amount1).plus(amount2);

// Bad: Never use floating point for money
const total = amount1 + amount2; // Can cause rounding errors!
```

### Code Review Checklist

Before marking a task complete, verify:

- [ ] Code follows project conventions
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] No sensitive data is committed
- [ ] Error handling is implemented
- [ ] Input validation is present
- [ ] Logging is appropriate
- [ ] Security best practices followed
- [ ] Performance is acceptable
- [ ] Code is reviewed for edge cases

## Useful Commands

### Development
```bash
# Install dependencies
npm install  # or pip install -r requirements.txt

# Run development server
npm run dev

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Lint code
npm run lint

# Format code
npm run format

# Build for production
npm run build
```

### Database
```bash
# Run migrations
npm run migrate

# Rollback migration
npm run migrate:rollback

# Seed database
npm run seed

# Reset database (careful!)
npm run db:reset
```

### Git
```bash
# Create feature branch
git checkout -b feature/description

# Commit changes
git add .
git commit -m "feat: description"

# Push to remote
git push -u origin feature/description

# Update from main
git fetch origin
git rebase origin/main
```

## Resources

### Documentation
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [REST API Design Guide](https://restfulapi.net/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### Financial App Specific
- [PCI DSS Compliance](https://www.pcisecuritystandards.org/)
- [Financial Data Security Standards](https://www.iso.org/standard/75652.html)

## Change Log

### 2025-11-15
- Initial CLAUDE.md created
- Established project structure and conventions
- Defined security guidelines
- Set up development workflow

---

**Last Updated**: 2025-11-15
**Maintained By**: AI Assistants and Project Contributors
**Version**: 1.0.0
