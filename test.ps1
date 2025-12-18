# python -m unittest discover tests
$ErrorActionPreference = "Stop"
python .\main.py insert Applications OnlineApplicationsUAT 22689 `
    -f FK_ApplicationNote_User_UserId `
    -f FK_ApplicationProgramIntake_ProgramIntakes_ProgramIntakeId `
    -f FK_Notifications_ProgramIntakes_ProgramIntakeId `
    -f FK_ApplicationDocuments_DocumentMetadata_MetadataId `
    -f FK_Applications_Agency_AgencyId `
    -f FK_Applications_PersonOrOrganization_AuthorizedPersonOrOrganizationId `
    -f FK_Notifications_CommunicationTemplate_QueuedTemplateId `
    -f FK_Notifications_User_QueuedUserId `
    -f FK_ProgramIntakes_Intakes_IntakeId `
    -f FK_NotificationAttachments_DocumentMetadata_DocumentMetadataId `
    -t > .\output\2025-11-05-test.sql