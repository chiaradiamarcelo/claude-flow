package banking.domain.models.account

interface JsonSchemaValidatorPort {
    fun isValidJson(payload: String): Boolean
}
