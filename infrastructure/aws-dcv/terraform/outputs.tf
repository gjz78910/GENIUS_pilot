output "artifact_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}

output "dcv_urls" {
  value = {
    for participant_id, instance in aws_instance.participant :
    participant_id => var.enable_trusted_dcv_cert ? "https://${local.participant_hostnames[participant_id]}:8443/#genius" : "https://${instance.public_dns}:8443/#genius"
  }
}

output "dcv_hostnames" {
  value = {
    for participant_id, hostname in local.participant_hostnames :
    participant_id => hostname
  }
}

output "instance_ids" {
  value = {
    for participant_id, instance in aws_instance.participant :
    participant_id => instance.id
  }
}

output "participant_password_parameters" {
  value = {
    for participant_id, parameter in aws_ssm_parameter.participant_password :
    participant_id => parameter.name
  }
}

output "end_session_document_name" {
  value = aws_ssm_document.end_session.name
}

output "end_session_commands" {
  value = {
    for participant_id, participant in local.participants :
    participant_id => "aws ssm send-command --document-name ${aws_ssm_document.end_session.name} --instance-ids ${aws_instance.participant[participant_id].id} --parameters participantId=${participant.participant_id},sessionId=${participant.session_id} --region ${var.aws_region}"
  }
}
