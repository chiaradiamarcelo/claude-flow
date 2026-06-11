package banking.application

import banking.domain.models.customer.CustomerRepository

class RegisterCustomerUseCase(
    private val customers: CustomerRepository,
) {
    fun execute(
        emailAddress: String,
        phoneNumber: String,
        countryCode: String,
        openingBalanceCents: Long,
        currencyCode: String,
    ): String {
        val customerId = customers.nextId()
        customers.register(customerId, emailAddress, phoneNumber, countryCode, openingBalanceCents, currencyCode)
        return customerId
    }
}
