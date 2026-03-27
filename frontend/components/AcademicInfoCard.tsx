import { Box, VStack, Text, Wrap } from '@chakra-ui/react';
import type { UserProfile } from '@/data/mock-profile';

interface AcademicInfoCardProps {
  profile: UserProfile;
}

export function AcademicInfoCard({ profile }: AcademicInfoCardProps) {
  return (
    <Box bg="gray.100" borderRadius="13px" p="24px" w="344px" flexShrink={0}>
      <VStack align="start" gap="16px">
        <Text
          fontSize="md"
          fontWeight="bold"
          color="gray.900"
          lineHeight="30px"
        >
          Academic Information
        </Text>

        <VStack align="start" gap="12px" w="100%">
          {/* Major */}
          <VStack align="start" gap="2px">
            <Text fontSize="sm" color="gray.500" lineHeight="24px">
              Major
            </Text>
            <Text fontSize="sm" color="gray.900" lineHeight="24px">
              {profile.major}
            </Text>
          </VStack>

          {/* Graduation Year */}
          <VStack align="start" gap="2px">
            <Text fontSize="sm" color="gray.500" lineHeight="24px">
              Graduation Year
            </Text>
            <Text fontSize="sm" color="gray.900" lineHeight="24px">
              {profile.graduationYear}
            </Text>
          </VStack>

          {/* UF Courses */}
          <VStack align="start" gap="8px" w="100%">
            <Text fontSize="sm" color="gray.500" lineHeight="24px">
              UF Courses
            </Text>
            <Wrap gap="8px">
              {profile.courses.map((course) => (
                <Box
                  key={course}
                  bg="white"
                  border="1.6px solid"
                  borderColor="orange.200"
                  borderRadius="8px"
                  px="10px"
                  py="6px"
                >
                  <Text fontSize="sm" color="gray.900" lineHeight="24px">
                    {course}
                  </Text>
                </Box>
              ))}
            </Wrap>
          </VStack>
        </VStack>
      </VStack>
    </Box>
  );
}
